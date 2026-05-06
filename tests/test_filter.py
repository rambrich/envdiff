"""Tests for envdiff.filter module."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.filter import (
    filter_by_key_pattern,
    filter_by_status,
    filter_diff_result,
)


@pytest.fixture()
def entries() -> list[DiffEntry]:
    return [
        DiffEntry(key="DB_HOST", status=DiffStatus.MATCH, source_value="localhost", target_value="localhost"),
        DiffEntry(key="DB_PORT", status=DiffStatus.MISMATCH, source_value="5432", target_value="3306"),
        DiffEntry(key="SECRET_KEY", status=DiffStatus.MISSING_IN_TARGET, source_value="abc", target_value=None),
        DiffEntry(key="API_URL", status=DiffStatus.MISSING_IN_SOURCE, source_value=None, target_value="https://api.example.com"),
        DiffEntry(key="API_KEY", status=DiffStatus.MISSING_IN_TARGET, source_value="xyz", target_value=None),
    ]


@pytest.fixture()
def diff_result(entries: list[DiffEntry]) -> DiffResult:
    return DiffResult(source_name=".env.dev", target_name=".env.prod", entries=entries)


def test_filter_by_status_single(entries):
    result = filter_by_status(entries, [DiffStatus.MATCH])
    assert len(result) == 1
    assert result[0].key == "DB_HOST"


def test_filter_by_status_multiple(entries):
    result = filter_by_status(entries, [DiffStatus.MISSING_IN_TARGET, DiffStatus.MISSING_IN_SOURCE])
    assert len(result) == 3
    keys = {e.key for e in result}
    assert keys == {"SECRET_KEY", "API_URL", "API_KEY"}


def test_filter_by_status_empty_list(entries):
    result = filter_by_status(entries, [])
    assert result == []


def test_filter_by_key_pattern_exact(entries):
    result = filter_by_key_pattern(entries, "DB_HOST")
    assert len(result) == 1
    assert result[0].key == "DB_HOST"


def test_filter_by_key_pattern_wildcard(entries):
    result = filter_by_key_pattern(entries, "API_*")
    assert len(result) == 2
    keys = {e.key for e in result}
    assert keys == {"API_URL", "API_KEY"}


def test_filter_by_key_pattern_no_match(entries):
    result = filter_by_key_pattern(entries, "NONEXISTENT_*")
    assert result == []


def test_filter_diff_result_by_status_only(diff_result):
    filtered = filter_diff_result(diff_result, statuses=[DiffStatus.MISMATCH])
    assert isinstance(filtered, DiffResult)
    assert len(filtered.entries) == 1
    assert filtered.entries[0].key == "DB_PORT"


def test_filter_diff_result_by_pattern_only(diff_result):
    filtered = filter_diff_result(diff_result, key_pattern="DB_*")
    assert len(filtered.entries) == 2
    keys = {e.key for e in filtered.entries}
    assert keys == {"DB_HOST", "DB_PORT"}


def test_filter_diff_result_combined(diff_result):
    filtered = filter_diff_result(
        diff_result,
        statuses=[DiffStatus.MISSING_IN_TARGET],
        key_pattern="API_*",
    )
    assert len(filtered.entries) == 1
    assert filtered.entries[0].key == "API_KEY"


def test_filter_diff_result_preserves_names(diff_result):
    filtered = filter_diff_result(diff_result, statuses=[DiffStatus.MATCH])
    assert filtered.source_name == ".env.dev"
    assert filtered.target_name == ".env.prod"


def test_filter_diff_result_no_criteria_returns_all(diff_result):
    filtered = filter_diff_result(diff_result)
    assert len(filtered.entries) == len(diff_result.entries)
