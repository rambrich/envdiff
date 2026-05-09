"""Tests for envdiff.grouper."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.grouper import (
    GroupedEntries,
    GroupedResult,
    group_by_keys,
    group_by_prefix,
)


@pytest.fixture()
def entries() -> list[DiffEntry]:
    return [
        DiffEntry(key="DB_HOST", source_value="localhost", target_value="localhost", status=DiffStatus.MATCH),
        DiffEntry(key="DB_PORT", source_value="5432", target_value=None, status=DiffStatus.MISSING_IN_TARGET),
        DiffEntry(key="APP_DEBUG", source_value="true", target_value="false", status=DiffStatus.MISMATCH),
        DiffEntry(key="APP_NAME", source_value="myapp", target_value="myapp", status=DiffStatus.MATCH),
        DiffEntry(key="SECRET", source_value=None, target_value="abc", status=DiffStatus.MISSING_IN_SOURCE),
    ]


@pytest.fixture()
def diff_result(entries: list[DiffEntry]) -> DiffResult:
    return DiffResult(source="a.env", target="b.env", entries=entries)


def test_group_by_prefix_returns_grouped_result(diff_result: DiffResult) -> None:
    result = group_by_prefix(diff_result)
    assert isinstance(result, GroupedResult)


def test_group_by_prefix_source_and_target(diff_result: DiffResult) -> None:
    result = group_by_prefix(diff_result)
    assert result.source == "a.env"
    assert result.target == "b.env"


def test_group_by_prefix_db_group(diff_result: DiffResult) -> None:
    result = group_by_prefix(diff_result)
    assert "DB" in result.groups
    assert result.groups["DB"].count == 2


def test_group_by_prefix_app_group(diff_result: DiffResult) -> None:
    result = group_by_prefix(diff_result)
    assert "APP" in result.groups
    assert result.groups["APP"].count == 2


def test_group_by_prefix_ungrouped_label(diff_result: DiffResult) -> None:
    result = group_by_prefix(diff_result)
    assert "OTHER" in result.groups
    assert result.groups["OTHER"].entries[0].key == "SECRET"


def test_group_by_prefix_custom_separator(diff_result: DiffResult) -> None:
    entry = DiffEntry(key="DB.HOST", source_value="x", target_value="x", status=DiffStatus.MATCH)
    dr = DiffResult(source="a", target="b", entries=[entry])
    result = group_by_prefix(dr, separator=".")
    assert "DB" in result.groups


def test_group_by_prefix_custom_ungrouped_label(diff_result: DiffResult) -> None:
    result = group_by_prefix(diff_result, ungrouped_label="MISC")
    assert "MISC" in result.groups


def test_group_names_are_sorted(diff_result: DiffResult) -> None:
    result = group_by_prefix(diff_result)
    assert result.group_names == sorted(result.group_names)


def test_grouped_entries_count(diff_result: DiffResult) -> None:
    result = group_by_prefix(diff_result)
    total = sum(g.count for g in result.groups.values())
    assert total == len(diff_result.entries)


def test_group_by_keys_explicit_mapping(diff_result: DiffResult) -> None:
    mapping = {"database": ["DB_HOST", "DB_PORT"], "app": ["APP_DEBUG", "APP_NAME"]}
    result = group_by_keys(diff_result, mapping)
    assert result.groups["DATABASE"].count == 2
    assert result.groups["APP"].count == 2
    assert result.groups["OTHER"].count == 1


def test_group_by_keys_get_returns_none_for_missing(diff_result: DiffResult) -> None:
    result = group_by_prefix(diff_result)
    assert result.get("NONEXISTENT") is None


def test_grouped_entries_repr() -> None:
    ge = GroupedEntries(name="TEST")
    assert "TEST" in repr(ge)
