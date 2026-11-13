"""Authentification des agents par l'en-tête X-Agent-Key."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select

from app.db import SessionDep
from app.models import Agent
from app.security import hash_agent_key

# auto_error=False : on renvoie nous-mêmes un 401 avec un message en français.
agent_key_header = APIKeyHeader(name="X-Agent-Key", auto_error=False)


async def get_current_agent(
    session: SessionDep, key: Annotated[str | None, Depends(agent_key_header)]
) -> Agent:
    """Retrouve l'agent à partir de sa clé, ou refuse la requête (401)."""
    if not key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "En-tête X-Agent-Key manquant.")

    # On ne compare jamais la clé elle-même : on hache celle reçue et on cherche ce hash.
    agent = await session.scalar(select(Agent).where(Agent.key_hash == hash_agent_key(key)))
    if agent is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Clé d'agent invalide.")
    return agent


AgentDep = Annotated[Agent, Depends(get_current_agent)]
