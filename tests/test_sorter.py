"""Tests for envdiff.sorter module."""

import pytest
from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.sorter import (
    sort_entries_by_status,
    sort_entries_by_key,
    group_entries_by_status,
    sorted_diff_result,
)


@pytest.fixture
def mixed_entries():
    return [
        DiffEntry(key="ZEBRA", status=DiffStatus.OK, source_value="1", target_value="1"),
        DiffEntry(key="ALPHA", status=DiffStatus.MISMATCH, source_value="a", target_value="b"),
        DiffEntry(key="BETA", status=DiffStatus.MISSING_IN_TARGET, source_value="x", target_value=None),
        DiffEntry(key="GAMMA", status=DiffStatus.MISSING_IN_SOURCE, source_value=None, target_value="y"),
        DiffEntry(key="DELTA", status=DiffStatus.MISMATCH, source_value="c", target_value="d"),
    ]


@pytest.fixture
def diff_result(mixed_entries):
    return DiffResult(source_name=".env.dev", target_name=".env.prod", entries=mixed_entries)


def test_sort_by_status_priority(mixed_entries):
    sorted_e = sort_entries_by_status(mixed_entries)
    statuses = [e.status for e in sorted_e]
    first_missing_target = statuses.index(DiffStatus.MISSING_IN_TARGET)
    first_missing_source = statuses.index(DiffStatus.MISSING_IN_SOURCE)
    first_mismatch = statuses.index(DiffStatus.MISMATCH)
    first_ok = statuses.index(DiffStatus.OK)
    assert first_missing_target < first_missing_source < first_mismatch < first_ok


def test_sort_by_status_secondary_key_alphabetical(mixed_entries):
    sorted_e = sort_entries_by_status(mixed_entries)
    mismatches = [e.key for e in sorted_e if e.status == DiffStatus.MISMATCH]
    assert mismatches == sorted(mismatches)


def test_sort_by_key_alphabetical(mixed_entries):
    sorted_e = sort_entries_by_key(mixed_entries)
    keys = [e.key for e in sorted_e]
    assert keys == sorted(keys)


def test_group_entries_by_status_keys(mixed_entries):
    groups = group_entries_by_status(mixed_entries)
    assert set(groups.keys()) == {DiffStatus.OK, DiffStatus.MISMATCH, DiffStatus.MISSING_IN_TARGET, DiffStatus.MISSING_IN_SOURCE}


def test_group_entries_by_status_counts(mixed_entries):
    groups = group_entries_by_status(mixed_entries)
    assert len(groups[DiffStatus.OK]) == 1
    assert len(groups[DiffStatus.MISMATCH]) == 2
    assert len(groups[DiffStatus.MISSING_IN_TARGET]) == 1
    assert len(groups[DiffStatus.MISSING_IN_SOURCE]) == 1


def test_group_entries_sorted_within_group(mixed_entries):
    groups = group_entries_by_status(mixed_entries)
    mismatch_keys = [e.key for e in groups[DiffStatus.MISMATCH]]
    assert mismatch_keys == sorted(mismatch_keys)


def test_sorted_diff_result_by_status_returns_diff_result(diff_result):
    result = sorted_diff_result(diff_result, by="status")
    assert isinstance(result, DiffResult)
    assert result.source_name == diff_result.source_name
    assert result.target_name == diff_result.target_name


def test_sorted_diff_result_by_key(diff_result):
    result = sorted_diff_result(diff_result, by="key")
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_sorted_diff_result_default_is_status(diff_result):
    result_default = sorted_diff_result(diff_result)
    result_status = sorted_diff_result(diff_result, by="status")
    assert [e.key for e in result_default.entries] == [e.key for e in result_status.entries]
