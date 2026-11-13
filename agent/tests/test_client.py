"""Tests de l'envoi à l'API, avec une fausse session HTTP (aucun réseau)."""

import logging
from types import SimpleNamespace

import pytest
import requests

from xool_agent.client import send
from xool_agent.collect import Measure
from xool_agent.config import Config

CONFIG = Config(api_url="http://127.0.0.1:8000", agent_key="xool_cle-secrete")
MEASURE: Measure = {"hostname": "pc-test", "time": "2026-11-13T12:00:00+00:00", "cpu": 12.5}


class FakeSession:
    """Imite `requests.Session` : renvoie une réponse choisie ou lève une erreur."""

    def __init__(
        self, status_code: int = 201, text: str = "", error: Exception | None = None
    ) -> None:
        self.response = SimpleNamespace(status_code=status_code, text=text)
        self.error = error
        self.calls: list[tuple[str, dict[str, object]]] = []

    def post(self, url: str, **kwargs: object) -> SimpleNamespace:
        self.calls.append((url, kwargs))
        if self.error is not None:
            raise self.error
        return self.response


def test_batch_is_posted_with_the_agent_key() -> None:
    session = FakeSession(status_code=201)

    assert send(session, CONFIG, [MEASURE]) is True

    url, kwargs = session.calls[0]
    assert url == "http://127.0.0.1:8000/metrics"
    assert kwargs["json"] == [MEASURE]
    assert kwargs["headers"] == {"X-Agent-Key": "xool_cle-secrete"}
    assert kwargs["timeout"] is not None
    # La clé ne doit pas suivre une redirection vers une autre adresse.
    assert kwargs["allow_redirects"] is False


@pytest.mark.parametrize(
    "error",
    [requests.ConnectionError("connexion refusée"), requests.Timeout("trop long")],
    ids=["api_coupee", "api_muette"],
)
def test_network_error_returns_false(error: Exception) -> None:
    session = FakeSession(error=error)

    assert send(session, CONFIG, [MEASURE]) is False


@pytest.mark.parametrize("status_code", [302, 401, 422, 500])
def test_refused_batch_returns_false(status_code: int) -> None:
    session = FakeSession(status_code=status_code, text="refus")

    assert send(session, CONFIG, [MEASURE]) is False


def test_key_is_never_logged(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)

    send(FakeSession(status_code=401), CONFIG, [MEASURE])
    send(FakeSession(status_code=500, text="erreur"), CONFIG, [MEASURE])
    send(FakeSession(error=requests.ConnectionError("coupé")), CONFIG, [MEASURE])

    assert len(caplog.records) == 3
    assert "xool_cle-secrete" not in caplog.text
