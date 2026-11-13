"""Envoi des mesures à l'API Xool."""

import logging

import requests

from xool_agent.collect import Measure
from xool_agent.config import Config

logger = logging.getLogger(__name__)

# (connexion, lecture) en secondes : une API muette ne doit pas bloquer l'agent.
TIMEOUT = (5, 15)


def send(session: requests.Session, config: Config, measures: list[Measure]) -> bool:
    """Envoie un lot à `POST /metrics`. Renvoie True si l'API l'a accepté, False sinon.

    Ne lève jamais d'erreur réseau : c'est à l'appelant de décider quoi faire d'un échec.
    """
    try:
        response = session.post(
            f"{config.api_url}/metrics",
            json=measures,
            headers={"X-Agent-Key": config.agent_key},
            timeout=TIMEOUT,
            # Sans ça, une redirection ferait partir la clé vers une autre adresse.
            allow_redirects=False,
        )
    except requests.RequestException as error:
        logger.warning("API injoignable (%s) : %s", type(error).__name__, error)
        return False

    if 200 <= response.status_code < 300:
        return True
    if response.status_code == 401:
        logger.error("L'API refuse la clé d'agent (401) : vérifier agent_key.")
    else:
        # La réponse est seulement affichée, tronquée : l'agent n'exécute rien venant du serveur.
        logger.warning(
            "Envoi refusé par l'API : HTTP %s %s", response.status_code, response.text[:200]
        )
    return False
