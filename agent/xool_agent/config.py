"""Configuration de l'agent : fichier `config.toml`, puis variables d'environnement."""

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

# À côté du dossier xool_agent/ : `agent/config.toml` en développement.
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.toml"

DEFAULT_INTERVAL_SECONDS = 60
MIN_INTERVAL_SECONDS = 5
MAX_INTERVAL_SECONDS = 3600

# Nom du réglage dans config.toml -> variable d'environnement qui le remplace.
ENV_NAMES = {
    "api_url": "XOOL_API_URL",
    "agent_key": "XOOL_AGENT_KEY",
    "interval_seconds": "XOOL_INTERVAL_SECONDS",
}


class ConfigError(Exception):
    """Configuration absente ou invalide. Le message est écrit pour l'utilisateur."""


@dataclass(frozen=True)
class Config:
    api_url: str
    # repr=False : la clé n'apparaît pas si un jour on affiche ou on logge l'objet.
    agent_key: str = field(repr=False)
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS


def _read_file(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as file:
            values = tomllib.load(file)
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{path} n'est pas un fichier TOML valide : {error}") from error

    # Un réglage mal orthographié serait ignoré en silence : on préfère refuser de démarrer.
    unknown = sorted(values.keys() - ENV_NAMES.keys())
    if unknown:
        raise ConfigError(f"Réglage inconnu dans {path} : {', '.join(unknown)}")
    return values


def _parse_api_url(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("api_url est obligatoire (exemple : https://api.xool.sn).")
    url = value.strip().rstrip("/")
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ConfigError(f"api_url doit commencer par http:// ou https:// (reçu : {url}).")
    return url


def _parse_agent_key(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(
            "agent_key est obligatoire : c'est la clé affichée à la création de l'agent."
        )
    return value.strip()


def _parse_interval(value: object) -> int:
    if value is None:
        return DEFAULT_INTERVAL_SECONDS
    # Depuis une variable d'environnement, la valeur arrive sous forme de texte.
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value)
    # bool est un sous-type d'int en Python : `true` ne doit pas passer pour 1 seconde.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError("interval_seconds doit être un nombre entier de secondes.")
    if not MIN_INTERVAL_SECONDS <= value <= MAX_INTERVAL_SECONDS:
        raise ConfigError(
            f"interval_seconds doit être entre {MIN_INTERVAL_SECONDS} et "
            f"{MAX_INTERVAL_SECONDS} secondes (reçu : {value})."
        )
    return value


def load_config(path: Path = DEFAULT_CONFIG_PATH, env: Mapping[str, str] | None = None) -> Config:
    """Lit `config.toml` s'il existe, puis laisse les variables d'environnement le remplacer."""
    env = os.environ if env is None else env
    values = _read_file(path)
    for name, env_name in ENV_NAMES.items():
        # Une variable vide (cas de `XOOL_AGENT_KEY=` dans un .env) ne remplace rien.
        if env.get(env_name):
            values[name] = env[env_name]

    return Config(
        api_url=_parse_api_url(values.get("api_url")),
        agent_key=_parse_agent_key(values.get("agent_key")),
        interval_seconds=_parse_interval(values.get("interval_seconds")),
    )
