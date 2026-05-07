"""Tests for envdiff.merger module."""

import pytest

from envdiff.differ import DiffStatus
from envdiff.merger import (
    MergeConflict,
    MergeStrategy,
    merge_envs,
    merge_to_entries,
)


ENV_A = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc"}
ENV_B = {"DB_HOST": "prod-db", "DB_PORT": "5432", "API_KEY": "xyz"}
ENV_C = {"DB_HOST": "staging-db", "DB_PORT": "5432", "SECRET": "abc", "API_KEY": "xyz"}


# ---------------------------------------------------------------------------
# merge_envs
# ---------------------------------------------------------------------------

def test_merge_envs_first_strategy_keeps_first_value():
    result = merge_envs({"a": ENV_A, "b": ENV_B}, MergeStrategy.FIRST)
    assert result["DB_HOST"] == "localhost"


def test_merge_envs_last_strategy_keeps_last_value():
    result = merge_envs({"a": ENV_A, "b": ENV_B}, MergeStrategy.LAST)
    assert result["DB_HOST"] == "prod-db"


def test_merge_envs_includes_all_keys():
    result = merge_envs({"a": ENV_A, "b": ENV_B}, MergeStrategy.FIRST)
    assert set(result.keys()) == {"DB_HOST", "DB_PORT", "SECRET", "API_KEY"}


def test_merge_envs_identical_values_no_conflict():
    result = merge_envs({"a": ENV_A, "b": ENV_B}, MergeStrategy.STRICT)
    assert result["DB_PORT"] == "5432"


def test_merge_envs_strict_raises_on_conflict():
    with pytest.raises(MergeConflict) as exc_info:
        merge_envs({"a": ENV_A, "b": ENV_B}, MergeStrategy.STRICT)
    assert exc_info.value.key == "DB_HOST"


def test_merge_conflict_stores_values():
    try:
        merge_envs({"a": ENV_A, "b": ENV_B}, MergeStrategy.STRICT)
    except MergeConflict as e:
        assert "localhost" in e.values.values()
        assert "prod-db" in e.values.values()


def test_merge_envs_single_source_returns_same():
    result = merge_envs({"a": ENV_A})
    assert result == ENV_A


def test_merge_envs_empty_returns_empty():
    result = merge_envs({})
    assert result == {}


# ---------------------------------------------------------------------------
# merge_to_entries
# ---------------------------------------------------------------------------

def test_merge_to_entries_returns_list():
    entries = merge_to_entries({"a": ENV_A, "b": ENV_B})
    assert isinstance(entries, list)


def test_merge_to_entries_all_keys_covered():
    entries = merge_to_entries({"a": ENV_A, "b": ENV_B})
    keys = {e.key for e in entries}
    assert keys == {"DB_HOST", "DB_PORT", "SECRET", "API_KEY"}


def test_merge_to_entries_match_status():
    entries = merge_to_entries({"a": ENV_A, "b": ENV_B})
    db_port = next(e for e in entries if e.key == "DB_PORT")
    assert db_port.status == DiffStatus.MATCH


def test_merge_to_entries_mismatch_status():
    entries = merge_to_entries({"a": ENV_A, "b": ENV_B})
    db_host = next(e for e in entries if e.key == "DB_HOST")
    assert db_host.status == DiffStatus.MISMATCH


def test_merge_to_entries_missing_status():
    entries = merge_to_entries({"a": ENV_A, "b": ENV_B})
    secret = next(e for e in entries if e.key == "SECRET")
    assert secret.status == DiffStatus.MISSING_IN_TARGET


def test_merge_to_entries_sorted_by_key():
    entries = merge_to_entries({"a": ENV_A, "b": ENV_B})
    keys = [e.key for e in entries]
    assert keys == sorted(keys)
