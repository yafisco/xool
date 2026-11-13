"""Point d'entrée de l'agent : collecte une mesure, l'envoie, attend, recommence."""

import logging
import signal
import sys
import time
from collections.abc import Callable
from types import FrameType
from urllib.parse import urlsplit

import requests

from xool_agent.client import send
from xool_agent.collect import collect
from xool_agent.config import Config, ConfigError, load_config

logger = logging.getLogger("xool_agent")

# Durée de la toute première mesure du CPU (voir `collect`).
FIRST_CPU_SAMPLE_SECONDS = 1.0
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def run_cycle(session: requests.Session, config: Config, cpu_interval: float | None) -> bool:
    """Un tour : une mesure collectée, puis envoyée. Renvoie True si l'API l'a acceptée."""
    measure = collect(cpu_interval)
    sent = send(session, config, [measure])
    if sent:
        logger.info(
            "Mesure envoyée : cpu %s %%, ram %s %%, disque %s %%",
            measure["cpu"],
            measure["ram"],
            measure["disk"],
        )
    else:
        # Le tampon hors connexion (T6) gardera ces mesures au lieu de les perdre.
        logger.warning("Mesure de %s non envoyée : elle est perdue.", measure["time"])
    return sent


def run(
    config: Config,
    session: requests.Session,
    *,
    sleep: Callable[[float], None] = time.sleep,
    max_cycles: int | None = None,
) -> None:
    """Boucle de l'agent. `max_cycles` limite le nombre de tours (tests et essais)."""
    cpu_interval: float | None = FIRST_CPU_SAMPLE_SECONDS
    next_tick = time.monotonic()
    cycles = 0
    while True:
        try:
            run_cycle(session, config, cpu_interval)
        except Exception:
            # Un tour raté (capteur, disque, bug) ne doit pas arrêter la supervision.
            # Ctrl+C n'est pas une `Exception` : il traverse et arrête bien l'agent.
            logger.exception("Tour en échec, l'agent continue.")
        cpu_interval = None

        cycles += 1
        if max_cycles is not None and cycles >= max_cycles:
            return

        # On vise des instants fixes (départ + N x intervalle) : le temps passé à collecter
        # et à envoyer ne décale pas les mesures. Après une longue pause (mise en veille),
        # on repart de maintenant au lieu d'enchaîner les tours en retard.
        next_tick = max(next_tick + config.interval_seconds, time.monotonic())
        sleep(max(0.0, next_tick - time.monotonic()))


def warn_if_insecure(config: Config) -> None:
    parts = urlsplit(config.api_url)
    if parts.scheme == "http" and parts.hostname not in LOCAL_HOSTS:
        logger.warning(
            "api_url est en http:// vers une autre machine : la clé d'agent circule en clair. "
            "Utiliser https:// hors des essais locaux."
        )


def _stop(signum: int, frame: FrameType | None) -> None:
    # Même chemin que Ctrl+C, pour un arrêt demandé par le système (`kill`, arrêt de service).
    raise KeyboardInterrupt


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        config = load_config()
    except ConfigError as error:
        logger.error("Configuration invalide : %s", error)
        return 2

    warn_if_insecure(config)
    signal.signal(signal.SIGTERM, _stop)
    logger.info(
        "Agent Xool démarré : envoi vers %s toutes les %s s (Ctrl+C pour arrêter)",
        config.api_url,
        config.interval_seconds,
    )
    try:
        with requests.Session() as session:
            run(config, session)
    except KeyboardInterrupt:
        logger.info("Arrêt demandé : agent arrêté proprement.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
