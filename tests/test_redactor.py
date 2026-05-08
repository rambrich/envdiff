"""Tests for envdiff.redactor."""

from __future__ import annotations

import pytest

from envdiff.redactor import (
    DEFAULT_MASK,
    RedactorConfig,
    redact_env,
    redact_keys,
    redact_value,
)


# ---------------------------------------------------------------------------
# RedactorConfig.is_sensitive
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", [
    "PASSWORD",
    "db_password",
    "SECRET_KEY",
    "API_KEY",
    "auth_token",
    "PRIVATE_KEY",
    "AWS_SECRET",
    "user_credentials",
    "PASSPHRASE",
])
def test_is_sensitive_returns_true_for_known_patterns(key: str) -> None:
    config = RedactorConfig()
    assert config.is_sensitive(key) is True


@pytest.mark.parametrize("key", [
    "HOST",
    "PORT",
    "DATABASE_URL",
    "DEBUG",
    "APP_NAME",
])
def test_is_sensitive_returns_false_for_safe_keys(key: str) -> None:
    config = RedactorConfig()
    assert config.is_sensitive(key) is False


def test_custom_pattern_is_respected() -> None:
    config = RedactorConfig(patterns=[r"(?i)internal"])
    assert config.is_sensitive("INTERNAL_HOST") is True
    assert config.is_sensitive("PASSWORD") is False  # default not included


def test_custom_mask_stored() -> None:
    config = RedactorConfig(mask="<hidden>")
    assert config.mask == "<hidden>"


# ---------------------------------------------------------------------------
# redact_value
# ---------------------------------------------------------------------------

def test_redact_value_masks_sensitive_key() -> None:
    config = RedactorConfig()
    assert redact_value("DB_PASSWORD", "s3cr3t", config) == DEFAULT_MASK


def test_redact_value_keeps_safe_key() -> None:
    config = RedactorConfig()
    assert redact_value("HOST", "localhost", config) == "localhost"


def test_redact_value_none_stays_none() -> None:
    config = RedactorConfig()
    assert redact_value("SECRET", None, config) is None


# ---------------------------------------------------------------------------
# redact_env
# ---------------------------------------------------------------------------

def test_redact_env_masks_sensitive_values() -> None:
    env = {"HOST": "localhost", "DB_PASSWORD": "hunter2", "API_KEY": "abc123"}
    result = redact_env(env)
    assert result["HOST"] == "localhost"
    assert result["DB_PASSWORD"] == DEFAULT_MASK
    assert result["API_KEY"] == DEFAULT_MASK


def test_redact_env_returns_new_dict() -> None:
    env = {"HOST": "localhost"}
    result = redact_env(env)
    assert result is not env


def test_redact_env_uses_default_config_when_none_given() -> None:
    env = {"SECRET": "mysecret"}
    assert redact_env(env)["SECRET"] == DEFAULT_MASK


# ---------------------------------------------------------------------------
# redact_keys
# ---------------------------------------------------------------------------

def test_redact_keys_returns_only_sensitive() -> None:
    keys = ["HOST", "PORT", "DB_PASSWORD", "AUTH_TOKEN", "DEBUG"]
    sensitive = redact_keys(keys)
    assert "DB_PASSWORD" in sensitive
    assert "AUTH_TOKEN" in sensitive
    assert "HOST" not in sensitive
    assert "DEBUG" not in sensitive


def test_redact_keys_empty_input() -> None:
    assert redact_keys([]) == []
