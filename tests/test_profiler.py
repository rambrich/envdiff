"""Tests for envdiff.profiler."""

import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.profiler import (
    DiffProfile,
    EnvProfile,
    profile_diff,
    profile_env,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_env():
    return {
        "APP_NAME": "myapp",
        "PORT": "8080",
        "DEBUG": "true",
        "DATABASE_URL": "https://db.example.com",
        "SECRET": "",
        "WORKERS": "4",
    }


@pytest.fixture()
def diff_result():
    entries = [
        DiffEntry(key="APP_NAME", status=DiffStatus.MATCH, source_value="myapp", target_value="myapp"),
        DiffEntry(key="PORT", status=DiffStatus.MISMATCH, source_value="8080", target_value="9090"),
        DiffEntry(key="SECRET", status=DiffStatus.MISSING_IN_TARGET, source_value="abc", target_value=None),
        DiffEntry(key="NEW_KEY", status=DiffStatus.MISSING_IN_SOURCE, source_value=None, target_value="xyz"),
    ]
    return DiffResult(source_name="source", target_name="target", entries=entries)


# ---------------------------------------------------------------------------
# profile_env tests
# ---------------------------------------------------------------------------


def test_profile_env_returns_env_profile(sample_env):
    result = profile_env(sample_env, env_name="test")
    assert isinstance(result, EnvProfile)


def test_profile_env_name(sample_env):
    result = profile_env(sample_env, env_name="staging")
    assert result.env_name == "staging"


def test_profile_env_total_keys(sample_env):
    result = profile_env(sample_env)
    assert result.total_keys == len(sample_env)


def test_profile_env_detects_empty_values(sample_env):
    result = profile_env(sample_env)
    assert "SECRET" in result.empty_value_keys
    assert result.empty_count == 1


def test_profile_env_detects_numeric_values(sample_env):
    result = profile_env(sample_env)
    assert "PORT" in result.numeric_value_keys
    assert "WORKERS" in result.numeric_value_keys
    assert result.numeric_count == 2


def test_profile_env_detects_boolean_values(sample_env):
    result = profile_env(sample_env)
    assert "DEBUG" in result.boolean_value_keys
    assert result.boolean_count == 1


def test_profile_env_detects_url_values(sample_env):
    result = profile_env(sample_env)
    assert "DATABASE_URL" in result.url_value_keys
    assert result.url_count == 1


def test_profile_env_plain_string_not_categorised(sample_env):
    result = profile_env(sample_env)
    assert "APP_NAME" not in result.empty_value_keys
    assert "APP_NAME" not in result.numeric_value_keys
    assert "APP_NAME" not in result.boolean_value_keys
    assert "APP_NAME" not in result.url_value_keys


def test_profile_env_empty_dict():
    result = profile_env({}, env_name="empty")
    assert result.total_keys == 0
    assert result.empty_count == 0


# ---------------------------------------------------------------------------
# profile_diff tests
# ---------------------------------------------------------------------------


def test_profile_diff_returns_diff_profile(diff_result):
    result = profile_diff(diff_result)
    assert isinstance(result, DiffProfile)


def test_profile_diff_source_name(diff_result):
    result = profile_diff(diff_result)
    assert result.source_profile.env_name == "source"


def test_profile_diff_target_name(diff_result):
    result = profile_diff(diff_result)
    assert result.target_profile.env_name == "target"


def test_profile_diff_overlap_count(diff_result):
    result = profile_diff(diff_result)
    # MATCH + MISMATCH both count as overlap
    assert result.overlap_count == 2


def test_profile_diff_unique_to_source(diff_result):
    result = profile_diff(diff_result)
    assert result.unique_to_source == 1


def test_profile_diff_unique_to_target(diff_result):
    result = profile_diff(diff_result)
    assert result.unique_to_target == 1
