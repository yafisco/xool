"""Crée un agent (et son organisation si besoin) et affiche sa clé une seule fois.

Usage, depuis le dossier api/ :
    uv run python -m scripts.create_agent --org "Clinique Exemple" --name "serveur-accueil"
"""

import argparse
import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_engine, get_session_factory
from app.models import Agent, Organization
from app.security import generate_agent_key, hash_agent_key


async def create_agent(session: AsyncSession, org_name: str, agent_name: str) -> str:
    """Crée l'agent et renvoie sa clé en clair. Seul le hash de la clé est écrit en base."""
    organization = await session.scalar(select(Organization).where(Organization.name == org_name))
    if organization is None:
        organization = Organization(name=org_name)
        session.add(organization)
        await session.flush()  # envoie l'INSERT pour obtenir organization.id

    existing = await session.scalar(
        select(Agent).where(Agent.organization_id == organization.id, Agent.name == agent_name)
    )
    if existing is not None:
        raise ValueError(f"L'agent « {agent_name} » existe déjà dans « {org_name} ».")

    key = generate_agent_key()
    session.add(
        Agent(organization_id=organization.id, name=agent_name, key_hash=hash_agent_key(key))
    )
    await session.commit()
    return key


async def run(org_name: str, agent_name: str) -> str:
    try:
        async with get_session_factory()() as session:
            return await create_agent(session, org_name, agent_name)
    finally:
        await get_engine().dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Crée un agent Xool et affiche sa clé.")
    parser.add_argument("--org", required=True, help="nom de l'organisation (créée si absente)")
    parser.add_argument("--name", required=True, help="nom de l'agent")
    args = parser.parse_args()

    try:
        key = asyncio.run(run(args.org, args.name))
    except ValueError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    # print et non logging : c'est un outil en ligne de commande, et la clé ne doit
    # surtout pas finir dans un fichier de logs.
    print(f"Agent « {args.name} » créé dans « {args.org} ».")
    print(f"Clé (à copier maintenant, elle ne sera plus jamais affichée) : {key}")
    print("À mettre dans XOOL_AGENT_KEY du fichier .env de l'agent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
