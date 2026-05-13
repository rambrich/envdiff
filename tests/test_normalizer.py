"""Tests for envdiff.normalizer."""

import pytest

from envdiff.normalizer import (
    NormalizeRecord,
    NormalizeResult,
    _normalize_value,
    normalize_env,
)


# ---------------------------------------------------------------------------
# _normalize_value unit tests
# ---------------------------------------------------------------------------

def test_normalize_strips_leading_trailing_whitespace():
    assert _normalize_value("  hello  ") == "hello"


def test_normalize_removes_double_quotes():
    assert _normalize_value('"my value"') == "my value"


def test_normalize_removes_single_quotes():
    assert _normalize_value("'my value'") == "my value"


def test_normalize_leaves_unquoted_value_unchanged():
    assert _normalize_value("plain") == "plain"


def test_normalize_does_not_strip_mismatched_quotes():
    assert _normalize_value('"bad\'') == '"bad\''


def test_normalize_empty_string():
    assert _normalize_value("") == ""


def test_normalize_single_char_not_unquoted():
    # A single quote char is length 1, not 2 — should not be stripped
    assert _normalize_value('"') == '"'


# ---------------------------------------------------------------------------
# normalize_env tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_env():
    return {
        "DB_HOST": '"localhost"',
        "DB_PORT": "  5432  ",
        "APP_NAME": "myapp",
        "SECRET": "'s3cr3t'",
    }


def test_normalize_env_returns_normalize_result(sample_env):
    result = normalize_env(sample_env)
    assert isinstance(result, NormalizeResult)


def test_normalize_env_name_stored(sample_env):
    result = normalize_env(sample_env, env_name="production")
    assert result.env_name == "production"


def test_normalize_env_record_count(sample_env):
    result = normalize_env(sample_env)
    assert len(result.records) == len(sample_env)


def test_normalize_env_records_are_normalize_record(sample_env):
    result = normalize_env(sample_env)
    assert all(isinstance(r, NormalizeRecord) for r in result.records)


def test_normalize_env_changed_count(sample_env):
    result = normalize_env(sample_env)
    # DB_HOST (double-quoted), DB_PORT (whitespace), SECRET (single-quoted) change
    assert result.changed_count == 3


def test_normalize_env_unchanged_count(sample_env):
    result = normalize_env(sample_env)
    assert result.unchanged_count == 1  # APP_NAME is already clean


def test_normalize_env_output_env_unquoted(sample_env):
    result = normalize_env(sample_env)
    assert result.output_env["DB_HOST"] == "localhost"
    assert result.output_env["SECRET"] == "s3cr3t"


def test_normalize_env_output_env_trimmed(sample_env):
    result = normalize_env(sample_env)
    assert result.output_env["DB_PORT"] == "5432"


def test_normalize_env_output_env_keys_match(sample_env):
    result = normalize_env(sample_env)
    assert set(result.output_env.keys()) == set(sample_env.keys())


def test_normalize_env_keys_sorted(sample_env):
    result = normalize_env(sample_env)
    keys = [r.key for r in result.records]
    assert keys == sorted(keys)


def test_normalize_record_changed_flag():
    record = NormalizeRecord(key="K", original='"v"', normalized="v")
    assert record.changed is True


def test_normalize_record_unchanged_flag():
    record = NormalizeRecord(key="K", original="v", normalized="v")
    assert record.changed is False
