"""Tests de la collecte : mesure réelle de la machine qui lance les tests."""

from datetime import UTC, datetime
from types import SimpleNamespace

import psutil
import pytest

from xool_agent.collect import collect, read_temperature, system_disk_path

# Les champs acceptés par `POST /metrics` (voir api/app/schemas.py).
EXPECTED_KEYS = {"hostname", "time", "cpu", "ram", "disk", "temperature", "uptime_h", "online"}


def fake_sensors(**sensors: list[float]) -> object:
    """Remplace `psutil.sensors_temperatures` par des capteurs inventés."""
    readings = {
        name: [SimpleNamespace(current=value) for value in values]
        for name, values in sensors.items()
    }
    return lambda: readings


def test_collect_returns_the_expected_keys() -> None:
    assert collect().keys() == EXPECTED_KEYS


def test_percentages_are_within_bounds() -> None:
    measure = collect(cpu_interval=0.1)

    for name in ("cpu", "ram", "disk"):
        value = measure[name]
        assert isinstance(value, float)
        assert 0 <= value <= 100


def test_time_is_utc_with_timezone() -> None:
    before = datetime.now(UTC).replace(microsecond=0)

    time = datetime.fromisoformat(str(collect()["time"]))

    assert time.utcoffset() is not None
    assert time.utcoffset().total_seconds() == 0
    assert time >= before


def test_other_fields_are_valid() -> None:
    measure = collect()

    assert isinstance(measure["hostname"], str)
    assert 1 <= len(measure["hostname"]) <= 255
    assert isinstance(measure["uptime_h"], float)
    assert measure["uptime_h"] >= 0
    assert measure["online"] is True
    temperature = measure["temperature"]
    assert temperature is None or -50 <= temperature <= 150


def test_system_disk_exists() -> None:
    assert psutil.disk_usage(system_disk_path()).total > 0


def test_temperature_is_none_without_sensor_support(monkeypatch: pytest.MonkeyPatch) -> None:
    # Cas de Windows : la fonction n'existe pas du tout dans psutil.
    monkeypatch.delattr(psutil, "sensors_temperatures", raising=False)

    assert read_temperature() is None


def test_temperature_is_none_without_any_sensor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(psutil, "sensors_temperatures", fake_sensors(), raising=False)

    assert read_temperature() is None


def test_temperature_prefers_the_cpu_sensor(monkeypatch: pytest.MonkeyPatch) -> None:
    sensors = fake_sensors(nvme=[70.0], coretemp=[48.0, 52.5, 50.0])
    monkeypatch.setattr(psutil, "sensors_temperatures", sensors, raising=False)

    assert read_temperature() == 52.5


def test_absurd_temperature_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    # Un capteur défectueux ne doit pas faire refuser tout le lot par l'API.
    monkeypatch.setattr(
        psutil, "sensors_temperatures", fake_sensors(coretemp=[999.0]), raising=False
    )

    assert read_temperature() is None


def test_unreadable_sensors_give_none(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken() -> object:
        raise OSError("capteur illisible")

    monkeypatch.setattr(psutil, "sensors_temperatures", broken, raising=False)

    assert read_temperature() is None
