"""Tests for envdiff.sanitizer."""
import pytest
from envdiff.sanitizer import (
    SanitizeRecord,
    SanitizeResult,
    sanitize_env,
)


@pytest.fixture()
def clean_env():
    return {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}


def test_sanitize_returns_sanitize_result(clean_env):
    result = sanitize_env(clean_env)
    assert isinstance(result, SanitizeResult)


def test_sanitize_env_name_stored(clean_env):
    result = sanitize_env(clean_env, env_name="production")
    assert result.env_name == "production"


def test_sanitize_clean_env_is_clean(clean_env):
    result = sanitize_env(clean_env)
    assert result.is_clean
    assert result.changed_count == 0


def test_sanitize_output_env_keys_match_input(clean_env):
    result = sanitize_env(clean_env)
    assert set(result.output_env.keys()) == set(clean_env.keys())


def test_sanitize_strips_control_characters():
    env = {"KEY": "val\x01ue"}
    result = sanitize_env(env, strip_control=True)
    assert result.output_env["KEY"] == "value"
    assert result.changed_count == 1


def test_sanitize_control_strip_disabled():
    env = {"KEY": "val\x01ue"}
    result = sanitize_env(env, strip_control=False)
    assert result.output_env["KEY"] == "val\x01ue"
    assert result.is_clean


def test_sanitize_replaces_newlines_by_default():
    env = {"MULTILINE": "line1\nline2"}
    result = sanitize_env(env)
    assert result.output_env["MULTILINE"] == "line1 line2"
    assert result.changed_count == 1


def test_sanitize_newline_replacement_custom():
    env = {"MULTILINE": "line1\nline2"}
    result = sanitize_env(env, newline_replacement="|")
    assert result.output_env["MULTILINE"] == "line1|line2"


def test_sanitize_replace_newlines_disabled():
    env = {"MULTILINE": "line1\nline2"}
    result = sanitize_env(env, replace_newlines=False)
    assert result.output_env["MULTILINE"] == "line1\nline2"


def test_sanitize_strip_whitespace():
    env = {"KEY": "  value  "}
    result = sanitize_env(env, strip_whitespace=True)
    assert result.output_env["KEY"] == "value"
    assert result.changed_count == 1


def test_sanitize_strip_whitespace_disabled():
    env = {"KEY": "  value  "}
    result = sanitize_env(env, strip_whitespace=False)
    assert result.output_env["KEY"] == "  value  "
    assert result.is_clean


def test_sanitize_custom_pattern():
    env = {"KEY": "hello123world"}
    result = sanitize_env(env, custom_pattern=r"\d+", custom_replacement="#")
    assert result.output_env["KEY"] == "hello#world"
    assert result.changed_count == 1


def test_sanitize_record_changed_false_when_unchanged():
    env = {"KEY": "clean"}
    result = sanitize_env(env)
    record = result.records[0]
    assert isinstance(record, SanitizeRecord)
    assert not record.changed


def test_sanitize_record_stores_original_and_sanitized():
    env = {"KEY": "val\x00ue"}
    result = sanitize_env(env)
    record = result.records[0]
    assert record.original == "val\x00ue"
    assert record.sanitized == "value"
