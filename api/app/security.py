"""Clés d'authentification des agents : génération et hachage."""

import hashlib
import secrets

AGENT_KEY_PREFIX = "xool_"


def generate_agent_key() -> str:
    """Génère une clé aléatoire (256 bits). Elle n'est montrée qu'une fois, à la création."""
    return AGENT_KEY_PREFIX + secrets.token_urlsafe(32)


def hash_agent_key(key: str) -> str:
    """Renvoie le SHA-256 de la clé en hexadécimal : c'est lui qu'on stocke en base.

    SHA-256 sans sel suffit ici parce que la clé est aléatoire et longue : on ne peut pas
    la deviner par dictionnaire. Pour un mot de passe choisi par un humain, il faudrait
    un algorithme lent (argon2, bcrypt).
    """
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
