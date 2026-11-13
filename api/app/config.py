"""Configuration de l'API, lue depuis l'environnement puis depuis le fichier .env racine."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Le .env vit à la racine du dépôt : il est partagé avec docker compose et l'agent.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Réglages de l'API. Une variable d'environnement prime sur le fichier .env."""

    # extra="ignore" : le .env contient aussi les variables de l'agent et de docker compose.
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    database_url: str


@lru_cache
def get_settings() -> Settings:
    """Charge les réglages une seule fois, au premier appel."""
    return Settings()
