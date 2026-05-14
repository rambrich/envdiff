"""Tests for envdiff.stripper."""
from __future__ import annotations

import pytest

from envdiff.stripper import StripRecord, StripResult, strip_keys


@pytest.fixture()
def reference() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_ENV": "prod"}


@pytest.fixture()
def target_env() -> dict:
    return {
        "DB_HOST": "remotehost",
        "DB_PORT": "5432",
        "APP_ENV": "staging",
        "LEGACY_KEY": "old_value",
        "UNUSED_VAR": "whatever",
    }


def test_strip_returns_strip_result(reference, target_env):
    result = strip_keys(target_env, reference)
    assert isinstance(result, StripResult)


def test_strip_env_name_default(reference, target_env):
    result = strip_keys(target_env, reference)
    assert result.env_name == "env"


def test_strip_env_name_custom(reference, target_env):
    result = strip_keys(target_env, reference, env_name="staging.env")
    assert result.env_name == "staging.env"


def test_strip_removes_unknown_keys(reference, target_env):
    result = strip_keys(target_env, reference)
    assert "LEGACY_KEY" not in result.output_env
    assert "UNUSED_VAR" not in result.output_env


def test_strip_retains_known_keys(reference, target_env):
    result = strip_keys(target_env, reference)
    assert "DB_HOST" in result.output_env
    assert "DB_PORT" in result.output_env
    assert "APP_ENV" in result.output_env


def test_strip_stripped_count(reference, target_env):
    result = strip_keys(target_env, reference)
    assert result.stripped_count == 2


def test_strip_stripped_records_are_strip_record(reference, target_env):
    result = strip_keys(target_env, reference)
    for rec in result.stripped:
        assert isinstance(rec, StripRecord)


def test_strip_stripped_keys_correct(reference, target_env):
    result = strip_keys(target_env, reference)
    stripped_keys = {r.key for r in result.stripped}
    assert stripped_keys == {"LEGACY_KEY", "UNUSED_VAR"}


def test_strip_is_clean_when_no_extras(reference):
    exact = dict(reference)
    result = strip_keys(exact, reference)
    assert result.is_clean


def test_strip_not_clean_when_extras(reference, target_env):
    result = strip_keys(target_env, reference)
    assert not result.is_clean


def test_strip_empty_target(reference):
    result = strip_keys({}, reference)
    assert result.is_clean
    assert result.output_env == {}


def test_strip_empty_reference(target_env):
    result = strip_keys(target_env, {})
    assert result.stripped_count == len(target_env)
    assert result.output_env == {}


def test_strip_values_preserved(reference, target_env):
    result = strip_keys(target_env, reference)
    assert result.output_env["DB_HOST"] == "remotehost"
