"""schema initial

Revision ID: 39c3475fb388
Revises:
Create Date: 2026-11-13 13:38:22.105877

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Identifiants de révision, utilisés par Alembic.
revision: str = "39c3475fb388"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organizations")),
        sa.UniqueConstraint("name", name=op.f("uq_organizations_name")),
    )
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_agents_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agents")),
        sa.UniqueConstraint("key_hash", name=op.f("uq_agents_key_hash")),
        sa.UniqueConstraint("organization_id", "name", name=op.f("uq_agents_organization_id_name")),
    )
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "server",
                "pc",
                "switch",
                "router",
                "ap",
                "ups",
                name="kind",
                native_enum=False,
                create_constraint=True,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("ip", postgresql.INET(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"], ["agents.id"], name=op.f("fk_devices_agent_id_agents")
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_devices_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_devices")),
        sa.UniqueConstraint("agent_id", "name", name=op.f("uq_devices_agent_id_name")),
    )
    op.create_index(
        op.f("ix_devices_organization_id"), "devices", ["organization_id"], unique=False
    )
    op.create_table(
        "metrics",
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cpu", sa.REAL(), nullable=True),
        sa.Column("ram", sa.REAL(), nullable=True),
        sa.Column("disk", sa.REAL(), nullable=True),
        sa.Column("temperature", sa.REAL(), nullable=True),
        sa.Column("uptime_h", sa.REAL(), nullable=True),
        sa.Column("online", sa.Boolean(), nullable=False),
        sa.CheckConstraint("cpu BETWEEN 0 AND 100", name=op.f("ck_metrics_cpu_range")),
        sa.CheckConstraint("disk BETWEEN 0 AND 100", name=op.f("ck_metrics_disk_range")),
        sa.CheckConstraint("ram BETWEEN 0 AND 100", name=op.f("ck_metrics_ram_range")),
        sa.CheckConstraint("uptime_h >= 0", name=op.f("ck_metrics_uptime_h_positive")),
        sa.ForeignKeyConstraint(
            ["device_id"], ["devices.id"], name=op.f("fk_metrics_device_id_devices")
        ),
        sa.PrimaryKeyConstraint("device_id", "time", name=op.f("pk_metrics")),
    )

    # Partie écrite à la main : Alembic ne connaît pas TimescaleDB.
    # Une hypertable découpe `metrics` en morceaux par tranche de temps (7 jours par défaut),
    # ce qui garde les requêtes rapides quand la table grossit.
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
    # create_default_indexes => false : la clé primaire (device_id, time) suffit, et on évite
    # un index créé hors d'Alembic que `--autogenerate` voudrait ensuite supprimer.
    op.execute(
        "SELECT create_hypertable('metrics', by_range('time'), create_default_indexes => false)"
    )


def downgrade() -> None:
    # Supprimer la table supprime aussi l'hypertable. L'extension reste installée.
    op.drop_table("metrics")
    op.drop_index(op.f("ix_devices_organization_id"), table_name="devices")
    op.drop_table("devices")
    op.drop_table("agents")
    op.drop_table("organizations")
