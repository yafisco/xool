"""Tests de GET /health, sans base réelle : la session est remplacée par une fausse."""

from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import get_session
from app.main import app


class FakeSession:
    """Imite la seule méthode de AsyncSession utilisée par /health."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    async def execute(self, statement: object) -> None:
        if self.error is not None:
            raise self.error


@pytest.fixture
def client_with() -> Iterator[Callable[[FakeSession], TestClient]]:
    """Fabrique un client de test dont la session de base est celle qu'on lui donne."""

    def build(session: FakeSession) -> TestClient:
        app.dependency_overrides[get_session] = lambda: session
        return TestClient(app)

    yield build
    app.dependency_overrides.clear()


def test_health_ok(client_with: Callable[[FakeSession], TestClient]) -> None:
    response = client_with(FakeSession()).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


@pytest.mark.parametrize(
    "error",
    [
        OperationalError("SELECT 1", {}, Exception("connexion perdue")),
        ConnectionRefusedError("connexion refusée"),
    ],
    ids=["erreur_sqlalchemy", "connexion_refusee"],
)
def test_health_db_down(client_with: Callable[[FakeSession], TestClient], error: Exception) -> None:
    response = client_with(FakeSession(error)).get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "db": "error"}
