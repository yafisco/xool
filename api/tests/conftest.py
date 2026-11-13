"""Fixtures partagées : une base de test jetable, créée par les migrations Alembic."""

import asyncio
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import URL, make_url, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import get_settings

API_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture
def anyio_backend() -> str:
    """Les tests marqués `anyio` tournent sur asyncio (anyio est fourni avec FastAPI)."""
    return "asyncio"


async def _run_admin_sql(admin_url: URL, statements: list[str]) -> None:
    # AUTOCOMMIT : CREATE/DROP DATABASE est interdit à l'intérieur d'une transaction.
    engine = create_async_engine(
        admin_url, isolation_level="AUTOCOMMIT", connect_args={"timeout": 5}
    )
    try:
        async with engine.connect() as connection:
            for statement in statements:
                await connection.execute(text(statement))
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def test_db_url() -> Iterator[str]:
    """Crée la base `<nom>_test`, y applique les migrations, puis la supprime à la fin.

    Les tests ne touchent donc jamais à la base de développement. Si aucune base n'est
    joignable (Docker arrêté), les tests qui en dépendent sont ignorés, pas en échec.
    """
    try:
        dev_url = make_url(get_settings().database_url)
    except ValueError as exc:  # DATABASE_URL absente : pas de .env
        pytest.skip(f"configuration de la base introuvable : {type(exc).__name__}")

    test_name = f"{dev_url.database}_test"
    test_url = dev_url.set(database=test_name).render_as_string(hide_password=False)
    drop = f'DROP DATABASE IF EXISTS "{test_name}" WITH (FORCE)'

    try:
        asyncio.run(_run_admin_sql(dev_url, [drop, f'CREATE DATABASE "{test_name}"']))
    except (SQLAlchemyError, OSError) as exc:
        pytest.skip(f"base de données injoignable : {type(exc).__name__}")

    alembic_config = Config(API_DIR / "alembic.ini")
    # % doublé : le fichier .ini traite % comme un caractère spécial.
    alembic_config.set_main_option("sqlalchemy.url", test_url.replace("%", "%%"))
    command.upgrade(alembic_config, "head")

    yield test_url

    asyncio.run(_run_admin_sql(dev_url, [drop]))


@pytest.fixture
async def session(test_db_url: str) -> AsyncIterator[AsyncSession]:
    """Session sur la base de test. Tout ce que le test écrit est annulé à la fin."""
    engine = create_async_engine(test_db_url)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        # create_savepoint : un commit() du code testé ne valide qu'un point de sauvegarde,
        # la transaction englobante reste ouverte et peut être annulée.
        async with AsyncSession(
            bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
        ) as db_session:
            yield db_session
        await transaction.rollback()
    await engine.dispose()
