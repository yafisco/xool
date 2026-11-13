"""Modèles SQLAlchemy : le schéma de la base. Toute modification passe par une migration Alembic."""

import enum
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address

from sqlalchemy import (
    REAL,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Identity,
    MetaData,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Noms de contraintes explicites et stables : Alembic en a besoin pour les modifier plus tard.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class DeviceKind(enum.StrEnum):
    SERVER = "server"
    PC = "pc"
    SWITCH = "switch"
    ROUTER = "router"
    AP = "ap"
    UPS = "ups"


class Organization(Base):
    """Un client de Xool (une PME, une école, une clinique…)."""

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Agent(Base):
    """Un programme de collecte installé chez un client. Il s'authentifie avec une clé."""

    __tablename__ = "agents"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(200))
    # SHA-256 de la clé en hexadécimal (64 caractères). La clé elle-même n'est jamais stockée.
    key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Device(Base):
    """Un équipement supervisé, vu par un agent."""

    __tablename__ = "devices"
    # Un agent identifie ses équipements par leur nom d'hôte.
    __table_args__ = (UniqueConstraint("agent_id", "name"),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    name: Mapped[str] = mapped_column(String(255))
    # native_enum=False : colonne texte + contrainte CHECK, plus simple à faire évoluer
    # par migration qu'un type ENUM PostgreSQL.
    kind: Mapped[DeviceKind] = mapped_column(
        Enum(
            DeviceKind,
            name="kind",
            native_enum=False,
            create_constraint=True,
            length=16,
            values_callable=lambda kinds: [kind.value for kind in kinds],
        )
    )
    ip: Mapped[IPv4Address | IPv6Address | None] = mapped_column(INET)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Metric(Base):
    """Une mesure d'un équipement à un instant donné. Hypertable TimescaleDB (voir la migration)."""

    __tablename__ = "metrics"
    __table_args__ = (
        CheckConstraint("cpu BETWEEN 0 AND 100", name="cpu_range"),
        CheckConstraint("ram BETWEEN 0 AND 100", name="ram_range"),
        CheckConstraint("disk BETWEEN 0 AND 100", name="disk_range"),
        CheckConstraint("uptime_h >= 0", name="uptime_h_positive"),
    )

    # Clé primaire (device_id, time) : un équipement ne peut pas avoir deux mesures au même
    # instant, donc un lot renvoyé deux fois par un agent ne crée pas de doublon.
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), primary_key=True)
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    # Pourcentages. Vides quand la mesure n'existe pas (un switch qu'on se contente de pinguer).
    cpu: Mapped[float | None] = mapped_column(REAL)
    ram: Mapped[float | None] = mapped_column(REAL)
    disk: Mapped[float | None] = mapped_column(REAL)
    temperature: Mapped[float | None] = mapped_column(REAL)
    uptime_h: Mapped[float | None] = mapped_column(REAL)
    online: Mapped[bool]
