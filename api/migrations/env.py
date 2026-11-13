"""Environnement Alembic : dit à Alembic à quelle base se connecter et quel schéma viser."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.models import Base

config = context.config

if config.config_file_name is not None:
    # disable_existing_loggers=False : ne pas couper les loggers de l'application ou des tests.
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Le schéma décrit par les modèles : Alembic le compare à la base pour `--autogenerate`.
target_metadata = Base.metadata


def get_url() -> str:
    """URL de la base : celle passée par le code appelant (les tests), sinon celle du .env."""
    return config.get_main_option("sqlalchemy.url") or get_settings().database_url


def run_migrations_offline() -> None:
    """Mode hors ligne (`alembic upgrade head --sql`) : écrit le SQL sans se connecter."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # NullPool : une migration ouvre une connexion, travaille, puis la ferme.
    connectable = create_async_engine(get_url(), poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
