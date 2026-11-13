"""Tests de POST /metrics, sur la base de test."""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, Device, DeviceKind, Metric
from app.schemas import MAX_BATCH_SIZE
from scripts.create_agent import create_agent

pytestmark = pytest.mark.anyio


def measure(minute: int = 0, **overrides: object) -> dict[str, object]:
    """Une mesure valide, que chaque test modifie selon son besoin."""
    return {
        "hostname": "pc-accueil",
        "time": f"2026-11-13T12:{minute:02d}:00Z",
        "cpu": 12.5,
        "ram": 48.0,
        "disk": 71.2,
        "temperature": 41.0,
        "uptime_h": 3.5,
        "online": True,
    } | overrides


async def count_metrics(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(Metric)) or 0


async def test_valid_batch_is_stored(
    client: AsyncClient, session: AsyncSession, agent_key: str
) -> None:
    response = await client.post(
        "/metrics", json=[measure(0), measure(1)], headers={"X-Agent-Key": agent_key}
    )

    assert response.status_code == 201
    assert response.json() == {"received": 2, "inserted": 2}

    metrics = (await session.scalars(select(Metric).order_by(Metric.time))).all()
    assert [metric.time for metric in metrics] == [
        datetime(2026, 11, 13, 12, 0, tzinfo=UTC),
        datetime(2026, 11, 13, 12, 1, tzinfo=UTC),
    ]
    assert metrics[0].cpu == pytest.approx(12.5)
    assert metrics[0].online is True


async def test_unknown_device_is_created_once(
    client: AsyncClient, session: AsyncSession, agent_key: str
) -> None:
    headers = {"X-Agent-Key": agent_key}
    await client.post("/metrics", json=[measure(0)], headers=headers)
    await client.post("/metrics", json=[measure(1)], headers=headers)

    devices = (await session.scalars(select(Device))).all()
    assert [(device.name, device.kind) for device in devices] == [("pc-accueil", DeviceKind.PC)]


async def test_agent_last_seen_is_updated(
    client: AsyncClient, session: AsyncSession, agent_key: str
) -> None:
    await client.post("/metrics", json=[measure()], headers={"X-Agent-Key": agent_key})

    last_seen_at = await session.scalar(select(Agent.last_seen_at))
    assert last_seen_at is not None


async def test_resent_batch_creates_no_duplicate(
    client: AsyncClient, session: AsyncSession, agent_key: str
) -> None:
    headers = {"X-Agent-Key": agent_key}
    batch = [measure(0), measure(1)]
    await client.post("/metrics", json=batch, headers=headers)

    # L'agent n'a pas reçu la réponse (coupure) : il renvoie le même lot, plus une mesure.
    response = await client.post("/metrics", json=[*batch, measure(2)], headers=headers)

    assert response.status_code == 201
    assert response.json() == {"received": 3, "inserted": 1}
    assert await count_metrics(session) == 3


async def test_same_hostname_under_two_agents_gives_two_devices(
    client: AsyncClient, session: AsyncSession, agent_key: str
) -> None:
    other_key = await create_agent(session, "Autre Organisation", "agent-autre")
    await client.post("/metrics", json=[measure()], headers={"X-Agent-Key": agent_key})
    await client.post("/metrics", json=[measure()], headers={"X-Agent-Key": other_key})

    assert await session.scalar(select(func.count()).select_from(Device)) == 2
    assert await count_metrics(session) == 2


@pytest.mark.parametrize(
    "headers",
    [{}, {"X-Agent-Key": ""}, {"X-Agent-Key": "xool_cle-inconnue"}],
    ids=["sans_en_tete", "cle_vide", "cle_inconnue"],
)
async def test_invalid_key_is_rejected(
    client: AsyncClient, session: AsyncSession, agent_key: str, headers: dict[str, str]
) -> None:
    response = await client.post("/metrics", json=[measure()], headers=headers)

    assert response.status_code == 401
    assert await count_metrics(session) == 0


@pytest.mark.parametrize(
    "overrides",
    [
        {"cpu": 150},
        {"ram": -1},
        {"disk": 100.1},
        {"uptime_h": -2},
        {"time": "2026-11-13T12:00:00"},
        {"hostname": ""},
        {"champ_inconnu": 1},
    ],
    ids=[
        "cpu_trop_haut",
        "ram_negative",
        "disque_trop_haut",
        "uptime_negatif",
        "heure_sans_fuseau",
        "nom_vide",
        "champ_inconnu",
    ],
)
async def test_invalid_measure_rejects_the_whole_batch(
    client: AsyncClient, session: AsyncSession, agent_key: str, overrides: dict[str, object]
) -> None:
    response = await client.post(
        "/metrics", json=[measure(0), measure(1, **overrides)], headers={"X-Agent-Key": agent_key}
    )

    assert response.status_code == 422
    assert await count_metrics(session) == 0


@pytest.mark.parametrize("size", [0, MAX_BATCH_SIZE + 1], ids=["lot_vide", "lot_trop_grand"])
async def test_batch_size_is_bounded(client: AsyncClient, agent_key: str, size: int) -> None:
    batch = [measure(hostname=f"pc-{index}") for index in range(size)]

    response = await client.post("/metrics", json=batch, headers={"X-Agent-Key": agent_key})

    assert response.status_code == 422
