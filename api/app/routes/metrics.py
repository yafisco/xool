"""Réception des mesures envoyées par les agents."""

from typing import Annotated

from fastapi import APIRouter, Body, status
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AgentDep
from app.db import SessionDep
from app.models import Agent, Device, DeviceKind, Metric
from app.schemas import MAX_BATCH_SIZE, IngestResult, MetricIn

router = APIRouter()

MetricBatch = Annotated[list[MetricIn], Body(min_length=1, max_length=MAX_BATCH_SIZE)]


async def _find_devices(session: AsyncSession, agent: Agent, hostnames: set[str]) -> dict[str, int]:
    rows = await session.execute(
        select(Device.name, Device.id).where(
            Device.agent_id == agent.id, Device.name.in_(hostnames)
        )
    )
    return {name: device_id for name, device_id in rows}


async def get_or_create_devices(
    session: AsyncSession, agent: Agent, hostnames: set[str]
) -> dict[str, int]:
    """Renvoie {nom d'hôte: id}, en créant les équipements que cet agent n'a jamais envoyés."""
    devices = await _find_devices(session, agent, hostnames)
    missing = hostnames - devices.keys()
    if not missing:
        return devices

    # ON CONFLICT DO NOTHING : si deux lots du même agent arrivent en même temps, le second
    # ne plante pas sur l'équipement que le premier vient de créer.
    await session.execute(
        insert(Device)
        .values(
            [
                {
                    "organization_id": agent.organization_id,
                    "agent_id": agent.id,
                    "name": hostname,
                    # Type par défaut, faute de mieux : il se corrigera depuis le dashboard.
                    "kind": DeviceKind.PC,
                }
                for hostname in sorted(missing)
            ]
        )
        .on_conflict_do_nothing(index_elements=["agent_id", "name"])
    )
    return await _find_devices(session, agent, hostnames)


@router.post("/metrics", status_code=status.HTTP_201_CREATED)
async def ingest_metrics(
    metrics: MetricBatch, agent: AgentDep, session: SessionDep
) -> IngestResult:
    """Enregistre un lot de mesures. Une mesure déjà reçue est ignorée, sans erreur."""
    devices = await get_or_create_devices(session, agent, {metric.hostname for metric in metrics})

    rows = [
        {"device_id": devices[metric.hostname], **metric.model_dump(exclude={"hostname"})}
        for metric in metrics
    ]
    # La clé primaire (device_id, time) détecte les doublons : un agent qui renvoie un lot
    # après une coupure ne crée pas de lignes en double (décision D006).
    result = await session.execute(
        insert(Metric).values(rows).on_conflict_do_nothing(index_elements=["device_id", "time"])
    )

    await session.execute(update(Agent).where(Agent.id == agent.id).values(last_seen_at=func.now()))
    await session.commit()
    return IngestResult(received=len(metrics), inserted=result.rowcount)
