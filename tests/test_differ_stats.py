"""Tests for envdiff.differ_stats."""
from __future__ import annotations

import pytest

from envdiff.differ import DiffResult, DiffEntry, DiffStatus
from envdiff.differ_stats import (
    KeyFrequency,
    DiffStatsResult,
    compute_diff_stats,
)


def _entry(key: str, status: DiffStatus) -> DiffEntry:
    sv = "v" if status != DiffStatus.MISSING_IN_SOURCE else None
    tv = "v" if status != DiffStatus.MISSING_IN_TARGET else None
    return DiffEntry(key=key, source_value=sv, target_value=tv, status=status)


def _result(*entries: DiffEntry) -> DiffResult:
    return DiffResult(
        source_name="src", target_name="tgt", entries=list(entries)
    )


# ---------------------------------------------------------------------------
# KeyFrequency
# ---------------------------------------------------------------------------

def test_key_frequency_total():
    kf = KeyFrequency(key="FOO", status_counts={"MATCH": 3, "MISMATCH": 1})
    assert kf.total == 4


def test_key_frequency_most_common_status():
    kf = KeyFrequency(key="FOO", status_counts={"MATCH": 5, "MISMATCH": 2})
    assert kf.most_common_status == "MATCH"


def test_key_frequency_most_common_status_empty():
    kf = KeyFrequency(key="FOO")
    assert kf.most_common_status == DiffStatus.MATCH.value


# ---------------------------------------------------------------------------
# compute_diff_stats
# ---------------------------------------------------------------------------

def test_compute_diff_stats_returns_diff_stats_result():
    r = _result(_entry("A", DiffStatus.MATCH))
    stats = compute_diff_stats([r])
    assert isinstance(stats, DiffStatsResult)


def test_compute_diff_stats_diff_count():
    r1 = _result(_entry("A", DiffStatus.MATCH))
    r2 = _result(_entry("A", DiffStatus.MISMATCH))
    stats = compute_diff_stats([r1, r2])
    assert stats.diff_count == 2


def test_compute_diff_stats_key_frequencies_count():
    r = _result(
        _entry("A", DiffStatus.MATCH),
        _entry("B", DiffStatus.MISSING_IN_TARGET),
    )
    stats = compute_diff_stats([r])
    assert len(stats.key_frequencies) == 2


def test_compute_diff_stats_status_counts_accumulated():
    r1 = _result(_entry("A", DiffStatus.MATCH))
    r2 = _result(_entry("A", DiffStatus.MISMATCH))
    r3 = _result(_entry("A", DiffStatus.MISMATCH))
    stats = compute_diff_stats([r1, r2, r3])
    kf = stats.key_frequencies[0]
    assert kf.status_counts[DiffStatus.MATCH.value] == 1
    assert kf.status_counts[DiffStatus.MISMATCH.value] == 2


def test_compute_diff_stats_most_volatile_key():
    r1 = _result(
        _entry("STABLE", DiffStatus.MATCH),
        _entry("FLAKY", DiffStatus.MISMATCH),
    )
    r2 = _result(
        _entry("STABLE", DiffStatus.MATCH),
        _entry("FLAKY", DiffStatus.MISSING_IN_TARGET),
    )
    stats = compute_diff_stats([r1, r2])
    assert stats.most_volatile_key == "FLAKY"


def test_compute_diff_stats_stable_keys():
    r1 = _result(
        _entry("ALWAYS_MATCH", DiffStatus.MATCH),
        _entry("SOMETIMES_BROKEN", DiffStatus.MISMATCH),
    )
    r2 = _result(
        _entry("ALWAYS_MATCH", DiffStatus.MATCH),
        _entry("SOMETIMES_BROKEN", DiffStatus.MATCH),
    )
    stats = compute_diff_stats([r1, r2])
    assert "ALWAYS_MATCH" in stats.stable_keys
    assert "SOMETIMES_BROKEN" not in stats.stable_keys


def test_compute_diff_stats_empty_list():
    stats = compute_diff_stats([])
    assert stats.diff_count == 0
    assert stats.key_frequencies == []
    assert stats.most_volatile_key is None
    assert stats.stable_keys == []
