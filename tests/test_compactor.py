"""Tests for envdiff.compactor."""
import pytest

from envdiff.compactor import CompactRecord, CompactResult, compact_envs


@pytest.fixture
def env_a() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_ENV": "dev"}


@pytest.fixture
def env_b() -> dict:
    return {"DB_HOST": "prod-db", "DB_PORT": "5432", "SECRET_KEY": "abc123"}


# --- CompactResult ---

def test_compact_result_output_env_keys(env_a, env_b):
    result = compact_envs([env_a, env_b], names=["a", "b"])
    assert set(result.output_env.keys()) == {"DB_HOST", "DB_PORT", "APP_ENV", "SECRET_KEY"}


def test_compact_result_env_name_stored(env_a):
    result = compact_envs([env_a], names=["a"], env_name="my-result")
    assert result.env_name == "my-result"


def test_compact_result_is_clean_when_no_conflicts(env_a):
    result = compact_envs([env_a], names=["a"])
    assert result.is_clean


def test_compact_result_not_clean_when_conflicts(env_a, env_b):
    result = compact_envs([env_a, env_b], names=["a", "b"])
    assert not result.is_clean


def test_compact_result_conflict_count(env_a, env_b):
    result = compact_envs([env_a, env_b], names=["a", "b"])
    # Only DB_HOST differs between a and b
    assert result.conflict_count == 1


# --- Priority (first-wins) ---

def test_compact_first_wins_by_default(env_a, env_b):
    result = compact_envs([env_a, env_b], names=["a", "b"])
    assert result.output_env["DB_HOST"] == "localhost"


def test_compact_prefer_last_wins(env_a, env_b):
    result = compact_envs([env_a, env_b], names=["a", "b"], prefer_last=True)
    assert result.output_env["DB_HOST"] == "prod-db"


# --- Identical values ---

def test_compact_identical_values_no_conflict(env_a, env_b):
    result = compact_envs([env_a, env_b], names=["a", "b"])
    db_port_record = next(r for r in result.records if r.key == "DB_PORT")
    assert db_port_record.alternatives == []


# --- Source name ---

def test_compact_record_source_name_first_wins(env_a, env_b):
    result = compact_envs([env_a, env_b], names=["a", "b"])
    db_host_record = next(r for r in result.records if r.key == "DB_HOST")
    assert db_host_record.source_name == "a"


def test_compact_record_source_name_prefer_last(env_a, env_b):
    result = compact_envs([env_a, env_b], names=["a", "b"], prefer_last=True)
    db_host_record = next(r for r in result.records if r.key == "DB_HOST")
    assert db_host_record.source_name == "b"


# --- Keys unique to one env ---

def test_compact_key_only_in_second_env_included(env_a, env_b):
    result = compact_envs([env_a, env_b], names=["a", "b"])
    assert "SECRET_KEY" in result.output_env


def test_compact_key_only_in_first_env_included(env_a, env_b):
    result = compact_envs([env_a, env_b], names=["a", "b"])
    assert "APP_ENV" in result.output_env


# --- Default names ---

def test_compact_default_names_generated():
    result = compact_envs([{"K": "1"}, {"K": "2"}])
    k_record = next(r for r in result.records if r.key == "K")
    assert k_record.source_name == "env0"


# --- Validation ---

def test_compact_mismatched_names_raises():
    with pytest.raises(ValueError, match="Length of 'names'"):
        compact_envs([{"A": "1"}], names=["x", "y"])


# --- Empty input ---

def test_compact_empty_envs_returns_empty_result():
    result = compact_envs([], names=[], env_name="empty")
    assert result.records == []
    assert result.is_clean
