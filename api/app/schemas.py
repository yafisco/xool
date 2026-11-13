"""Schémas Pydantic : la forme des données qui entrent et sortent de l'API."""

from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

# Nombre maximal de mesures par requête. À une mesure par minute, cela fait plus de 16 heures
# de tampon par envoi : un agent qui revient d'une longue coupure envoie plusieurs lots.
MAX_BATCH_SIZE = 1000

Percent = Annotated[float, Field(ge=0, le=100)]


class MetricIn(BaseModel):
    """Une mesure envoyée par un agent."""

    # extra="forbid" : un champ inconnu (faute de frappe côté agent) est refusé, pas ignoré.
    model_config = ConfigDict(extra="forbid")

    hostname: str = Field(min_length=1, max_length=255)
    # AwareDatetime : l'horodatage doit préciser son fuseau (ex. 2026-11-13T12:00:00Z).
    time: AwareDatetime
    cpu: Percent | None = None
    ram: Percent | None = None
    disk: Percent | None = None
    temperature: float | None = Field(default=None, ge=-50, le=150)
    uptime_h: float | None = Field(default=None, ge=0)
    online: bool = True


class IngestResult(BaseModel):
    """Réponse de POST /metrics."""

    received: int
    # Inférieur à `received` quand des mesures étaient déjà en base (lot renvoyé).
    inserted: int
