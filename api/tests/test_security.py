"""Tests des clés d'agent (sans base de données)."""

import hashlib

from app.security import AGENT_KEY_PREFIX, generate_agent_key, hash_agent_key


def test_generated_keys_are_unique_and_prefixed() -> None:
    keys = {generate_agent_key() for _ in range(100)}

    assert len(keys) == 100
    assert all(key.startswith(AGENT_KEY_PREFIX) for key in keys)


def test_hash_is_sha256_hex() -> None:
    key = "xool_exemple"

    assert hash_agent_key(key) == hashlib.sha256(b"xool_exemple").hexdigest()
    assert len(hash_agent_key(key)) == 64


def test_hash_differs_for_different_keys() -> None:
    assert hash_agent_key("xool_a") != hash_agent_key("xool_b")
