"""Tests du chargement de la configuration."""

from pathlib import Path

import pytest

from xool_agent.config import Config, ConfigError, load_config

VALID_FILE = """
api_url = "https://api.exemple.sn/"
agent_key = "xool_cle-du-fichier"
interval_seconds = 30
"""


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_config_is_read_from_file(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path, VALID_FILE), env={})

    # La barre oblique finale est retirée : l'agent ajoute lui-même `/metrics`.
    assert config == Config(
        api_url="https://api.exemple.sn", agent_key="xool_cle-du-fichier", interval_seconds=30
    )


def test_environment_overrides_file(tmp_path: Path) -> None:
    env = {"XOOL_AGENT_KEY": "xool_cle-env", "XOOL_INTERVAL_SECONDS": "120"}

    config = load_config(write_config(tmp_path, VALID_FILE), env=env)

    assert config.agent_key == "xool_cle-env"
    assert config.interval_seconds == 120
    assert config.api_url == "https://api.exemple.sn"


def test_environment_alone_is_enough(tmp_path: Path) -> None:
    env = {"XOOL_API_URL": "http://127.0.0.1:8000", "XOOL_AGENT_KEY": "xool_cle-env"}

    config = load_config(tmp_path / "absent.toml", env=env)

    assert config.interval_seconds == 60


def test_empty_environment_variable_does_not_override(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path, VALID_FILE), env={"XOOL_AGENT_KEY": ""})

    assert config.agent_key == "xool_cle-du-fichier"


def test_key_is_hidden_from_repr(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path, VALID_FILE), env={})

    assert "xool_cle-du-fichier" not in repr(config)


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ('api_url = "https://api.exemple.sn"', "agent_key"),
        ('agent_key = "xool_cle"', "api_url"),
        ('api_url = "api.exemple.sn"\nagent_key = "xool_cle"', "http"),
        (VALID_FILE.replace("30", "2"), "interval_seconds"),
        (VALID_FILE.replace("30", '"vite"'), "interval_seconds"),
        (VALID_FILE.replace("30", "true"), "interval_seconds"),
        (VALID_FILE + "interval = 60\n", "interval"),
        ("api_url = ", "TOML"),
    ],
    ids=[
        "cle_absente",
        "url_absente",
        "url_sans_http",
        "intervalle_trop_court",
        "intervalle_texte",
        "intervalle_booleen",
        "reglage_inconnu",
        "fichier_illisible",
    ],
)
def test_invalid_config_is_rejected(tmp_path: Path, content: str, expected: str) -> None:
    with pytest.raises(ConfigError, match=expected):
        load_config(write_config(tmp_path, content), env={})
