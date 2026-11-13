"""Point d'entrée de l'API Xool."""

import logging
from typing import Literal

from fastapi import FastAPI, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import SessionDep
from app.routes import metrics

logger = logging.getLogger(__name__)

app = FastAPI(title="Xool API", version="0.1.0")
app.include_router(metrics.router)


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    db: Literal["ok", "error"]


@app.get("/health", responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": Health}})
async def health(session: SessionDep, response: Response) -> Health:
    """Indique si l'API tourne et si elle peut joindre la base."""
    try:
        await session.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError) as exc:
        # OSError : asyncpg laisse remonter tel quel un refus de connexion ou un délai dépassé.
        logger.error("Base de données injoignable : %s", type(exc).__name__)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return Health(status="degraded", db="error")
    return Health(status="ok", db="ok")
