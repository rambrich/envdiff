"""Tests for envdiff.classifier."""
from __future__ import annotations

import pytest

from envdiff.classifier import (
    ClassifiedKey,
    ClassifyResult,
    _classify_key,
    classify_env,
)


@pytest.fixture()
def sample_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PASSWORD": "secret",
        "API_KEY": "abc123",
        "LOG_LEVEL": "INFO",
        "APP_PORT": "8080",
        "FEATURE_DARK_MODE": "true",
        "SMTP_HOST": "mail.example.com",
        "CUSTOM_VAR": "value",
    }


def test_classify_env_returns_classify_result(sample_env):
    result = classify_env(sample_env, env_name="test")
    assert isinstance(result, ClassifyResult)


def test_classify_env_name_stored(sample_env):
    result = classify_env(sample_env, env_name="production")
    assert result.env_name == "production"


def test_classify_env_entry_count(sample_env):
    result = classify_env(sample_env)
    assert len(result.entries) == len(sample_env)


def test_classify_env_entries_are_classified_keys(sample_env):
    result = classify_env(sample_env)
    for entry in result.entries:
        assert isinstance(entry, ClassifiedKey)


def test_classify_key_database():
    assert _classify_key("DB_HOST") == "database"
    assert _classify_key("DATABASE_URL") == "database"


def test_classify_key_auth():
    assert _classify_key("API_KEY") == "auth"
    assert _classify_key("JWT_SECRET") == "auth"


def test_classify_key_network():
    assert _classify_key("APP_PORT") == "network"
    assert _classify_key("BASE_URL") == "network"


def test_classify_key_feature_flag():
    assert _classify_key("FEATURE_DARK_MODE") == "feature_flag"
    assert _classify_key("ENABLE_SIGNUP") == "feature_flag"


def test_classify_key_logging():
    assert _classify_key("LOG_LEVEL") == "logging"


def test_classify_key_email():
    assert _classify_key("SMTP_HOST") == "email"
    assert _classify_key("MAIL_FROM") == "email"


def test_classify_key_other():
    assert _classify_key("CUSTOM_VAR") == "other"


def test_keys_for_category(sample_env):
    result = classify_env(sample_env)
    db_keys = result.keys_for_category("database")
    assert "DB_HOST" in db_keys


def test_categories_returns_sorted_list(sample_env):
    result = classify_env(sample_env)
    cats = result.categories()
    assert cats == sorted(cats)
    assert "other" in cats


def test_category_for_key(sample_env):
    result = classify_env(sample_env)
    assert result.category_for_key("LOG_LEVEL") == "logging"


def test_category_for_missing_key(sample_env):
    result = classify_env(sample_env)
    assert result.category_for_key("NONEXISTENT") is None


def test_custom_patterns():
    env = {"MY_CUSTOM_KEY": "val"}
    custom = {"custom_cat": [r"MY_CUSTOM"]}
    result = classify_env(env, patterns=custom)
    assert result.entries[0].category == "custom_cat"
