"""Tests de la boucle de l'agent, sans réseau ni attente réelle."""

import logging

import pytest
import requests

from xool_agent import main as agent_main
from xool_agent.collect import Measure
from xool_agent.config import Config, ConfigError

CONFIG = Config(api_url="http://127.0.0.1:8000", agent_key="xool_cle-secrete", interval_seconds=60)


def fake_measure(cpu_interval: float | None = None) -> Measure:
    return {
        "hostname": "pc-test",
        "time": "2026-11-13T12:00:00+00:00",
        "cpu": 1.0,
        "ram": 2.0,
        "disk": 3.0,
    }


class FakeClock:
    """Horloge de test : `sleep` avance le temps au lieu d'attendre, et note les durées."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, duration: float) -> None:
        self.sleeps.append(duration)
        self.now += duration


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    """Remplace la collecte par une mesure fixe et le temps par une horloge de test."""
    fake_clock = FakeClock()
    monkeypatch.setattr(agent_main, "collect", fake_measure)
    monkeypatch.setattr(agent_main.time, "monotonic", fake_clock.monotonic)
    return fake_clock


def test_loop_sends_one_measure_per_cycle(
    monkeypatch: pytest.MonkeyPatch, clock: FakeClock
) -> None:
    batches: list[list[Measure]] = []
    monkeypatch.setattr(
        agent_main, "send", lambda session, config, measures: batches.append(measures) or True
    )

    agent_main.run(CONFIG, requests.Session(), sleep=clock.sleep, max_cycles=3)

    assert batches == [[fake_measure()]] * 3
    # Une attente entre deux tours, aucune après le dernier.
    assert clock.sleeps == [60, 60]


def test_loop_keeps_a_steady_rhythm(monkeypatch: pytest.MonkeyPatch, clock: FakeClock) -> None:
    def slow_send(session: requests.Session, config: Config, measures: list[Measure]) -> bool:
        clock.now += 2  # l'envoi dure 2 secondes
        return True

    monkeypatch.setattr(agent_main, "send", slow_send)

    agent_main.run(CONFIG, requests.Session(), sleep=clock.sleep, max_cycles=3)

    # L'attente est raccourcie d'autant : une mesure toutes les 60 s, pas toutes les 62 s.
    assert clock.sleeps == [58, 58]


def test_loop_does_not_catch_up_after_a_long_pause(
    monkeypatch: pytest.MonkeyPatch, clock: FakeClock
) -> None:
    def frozen_send(session: requests.Session, config: Config, measures: list[Measure]) -> bool:
        clock.now += 600  # la machine a été en veille 10 minutes
        return True

    monkeypatch.setattr(agent_main, "send", frozen_send)

    agent_main.run(CONFIG, requests.Session(), sleep=clock.sleep, max_cycles=3)

    # Pas de rafale de tours pour rattraper le retard : on repart tout de suite, une fois.
    assert clock.sleeps == [0, 0]


def test_loop_survives_a_failed_send(monkeypatch: pytest.MonkeyPatch, clock: FakeClock) -> None:
    results = iter([False, True])
    monkeypatch.setattr(agent_main, "send", lambda session, config, measures: next(results))

    agent_main.run(CONFIG, requests.Session(), sleep=clock.sleep, max_cycles=2)

    assert clock.sleeps == [60]


def test_loop_survives_a_crashing_cycle(
    monkeypatch: pytest.MonkeyPatch, clock: FakeClock, caplog: pytest.LogCaptureFixture
) -> None:
    def broken_collect(cpu_interval: float | None = None) -> Measure:
        raise RuntimeError("capteur en panne")

    monkeypatch.setattr(agent_main, "collect", broken_collect)

    agent_main.run(CONFIG, requests.Session(), sleep=clock.sleep, max_cycles=3)

    assert clock.sleeps == [60, 60]
    assert "Tour en échec" in caplog.text


def test_first_cpu_sample_blocks_then_uses_the_interval(
    monkeypatch: pytest.MonkeyPatch, clock: FakeClock
) -> None:
    intervals: list[float | None] = []

    def recording_collect(cpu_interval: float | None = None) -> Measure:
        intervals.append(cpu_interval)
        return fake_measure()

    monkeypatch.setattr(agent_main, "collect", recording_collect)
    monkeypatch.setattr(agent_main, "send", lambda session, config, measures: True)

    agent_main.run(CONFIG, requests.Session(), sleep=clock.sleep, max_cycles=3)

    assert intervals == [agent_main.FIRST_CPU_SAMPLE_SECONDS, None, None]


def test_main_stops_cleanly_on_ctrl_c(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def interrupted(config: Config, session: requests.Session) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(agent_main, "load_config", lambda: CONFIG)
    monkeypatch.setattr(agent_main, "run", interrupted)
    monkeypatch.setattr(agent_main.signal, "signal", lambda signum, handler: None)
    caplog.set_level(logging.INFO)

    assert agent_main.main() == 0
    assert "arrêté proprement" in caplog.text
    assert "xool_cle-secrete" not in caplog.text


def test_main_refuses_an_invalid_config(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def invalid() -> Config:
        raise ConfigError("agent_key est obligatoire")

    monkeypatch.setattr(agent_main, "load_config", invalid)

    assert agent_main.main() == 2
    assert "agent_key est obligatoire" in caplog.text


def test_plain_http_to_another_machine_is_flagged(caplog: pytest.LogCaptureFixture) -> None:
    agent_main.warn_if_insecure(CONFIG)
    assert caplog.text == ""

    agent_main.warn_if_insecure(Config(api_url="http://api.exemple.sn", agent_key="xool_cle"))
    assert "en clair" in caplog.text
