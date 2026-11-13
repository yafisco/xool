"""Tests du schéma créé par les migrations, sur une vraie base PostgreSQL + TimescaleDB."""

from datetime import UTC, datetime
from ipaddress import IPv4Address

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, Device, DeviceKind, Metric, Organization
from app.security import hash_agent_key
from scripts.create_agent import create_agent

pytestmark = pytest.mark.anyio


async def _make_device(session: AsyncSession) -> Device:
    organization = Organization(name="Clinique Test")
    session.add(organization)
    await session.flush()
    agent = Agent(organization_id=organization.id, name="agent-1", key_hash=hash_agent_key("k"))
    session.add(agent)
    await session.flush()
    device = Device(
        organization_id=organization.id,
        agent_id=agent.id,
        name="srv-accueil",
        kind=DeviceKind.SERVER,
        ip=IPv4Address("192.168.1.10"),
    )
    session.add(device)
    await session.flush()
    return device


async def test_migration_creates_all_tables(session: AsyncSession) -> None:
    rows = await session.scalars(
        text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    )

    assert {"organizations", "agents", "devices", "metrics"} <= set(rows)


async def test_metrics_is_a_hypertable(session: AsyncSession) -> None:
    count = await session.scalar(
        text(
            "SELECT count(*) FROM timescaledb_information.hypertables "
            "WHERE hypertable_name = 'metrics'"
        )
    )

    assert count == 1


async def test_metric_roundtrip(session: AsyncSession) -> None:
    device = await _make_device(session)
    measured_at = datetime(2026, 11, 13, 12, 0, tzinfo=UTC)
    session.add(
        Metric(device_id=device.id, time=measured_at, cpu=42.5, ram=60.0, disk=71.0, online=True)
    )
    await session.flush()
    session.expunge_all()  # force une vraie relecture depuis la base

    metric = await session.scalar(select(Metric).where(Metric.device_id == device.id))
    stored_device = await session.get(Device, device.id)

    assert metric is not None and stored_device is not None
    assert metric.time == measured_at
    assert metric.cpu == pytest.approx(42.5)
    assert metric.temperature is None
    assert stored_device.kind is DeviceKind.SERVER
    assert stored_device.ip == IPv4Address("192.168.1.10")


async def test_metric_out_of_range_is_rejected(session: AsyncSession) -> None:
    device = await _make_device(session)
    session.add(
        Metric(device_id=device.id, time=datetime(2026, 11, 13, tzinfo=UTC), cpu=150, online=True)
    )

    with pytest.raises(IntegrityError, match="ck_metrics_cpu_range"):
        await session.flush()


async def test_duplicate_metric_is_rejected(session: AsyncSession) -> None:
    device = await _make_device(session)
    measured_at = datetime(2026, 11, 13, 12, 0, tzinfo=UTC)
    session.add(Metric(device_id=device.id, time=measured_at, online=True))
    await session.flush()
    session.expunge_all()
    session.add(Metric(device_id=device.id, time=measured_at, online=False))

    with pytest.raises(IntegrityError):
        await session.flush()


async def test_create_agent_stores_only_the_hash(session: AsyncSession) -> None:
    key = await create_agent(session, "École Test", "agent-labo")

    agent = await session.scalar(select(Agent).where(Agent.name == "agent-labo"))
    assert agent is not None
    assert agent.key_hash == hash_agent_key(key)
    assert key not in agent.key_hash
    assert agent.last_seen_at is None


async def test_create_agent_reuses_existing_organization(session: AsyncSession) -> None:
    await create_agent(session, "École Test", "agent-1")
    await create_agent(session, "École Test", "agent-2")

    organizations = (await session.scalars(select(Organization))).all()
    assert [organization.name for organization in organizations] == ["École Test"]


async def test_create_agent_refuses_duplicate_name(session: AsyncSession) -> None:
    await create_agent(session, "École Test", "agent-1")

    with pytest.raises(ValueError, match="existe déjà"):
        await create_agent(session, "École Test", "agent-1")
