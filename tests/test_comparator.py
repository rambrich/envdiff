"""Tests for envdiff.comparator."""
from __future__ import annotations

import pytest

from envdiff.comparator import CompareResult, compare_many
from envdiff.differ import DiffStatus


SOURCE = {"A": "1", "B": "2", "C": "3"}
TARGET_OK = {"A": "1", "B": "2", "C": "3"}
TARGET_MISSING = {"A": "1", "B": "2"}          # missing C
TARGET_MISMATCH = {"A": "1", "B": "X", "C": "3"}  # B mismatch
TARGET_EXTRA = {"A": "1", "B": "2", "C": "3", "D": "4"}  # D missing in source


def test_compare_many_returns_compare_result():
    result = compare_many(SOURCE, {"ok": TARGET_OK})
    assert isinstance(result, CompareResult)


def test_compare_many_source_name_stored():
    result = compare_many(SOURCE, {"ok": TARGET_OK}, source_name="prod")
    assert result.source_name == "prod"


def test_compare_many_target_names():
    result = compare_many(SOURCE, {"t1": TARGET_OK, "t2": TARGET_MISSING})
    assert set(result.target_names) == {"t1", "t2"}


def test_compare_many_no_issues_when_all_match():
    result = compare_many(SOURCE, {"ok": TARGET_OK})
    assert not result.has_any_issues()


def test_compare_many_has_issues_when_mismatch():
    result = compare_many(SOURCE, {"bad": TARGET_MISMATCH})
    assert result.has_any_issues()


def test_compare_many_has_issues_when_missing_in_target():
    result = compare_many(SOURCE, {"bad": TARGET_MISSING})
    assert result.has_any_issues()


def test_compare_many_summaries_populated():
    result = compare_many(SOURCE, {"t1": TARGET_OK, "t2": TARGET_MISSING})
    assert "t1" in result.summaries
    assert "t2" in result.summaries


def test_summary_counts_for_clean_target():
    result = compare_many(SOURCE, {"ok": TARGET_OK})
    s = result.summaries["ok"]
    assert s.match_count == 3
    assert s.missing_in_target_count == 0
    assert s.mismatch_count == 0


def test_summary_counts_for_missing_key():
    result = compare_many(SOURCE, {"bad": TARGET_MISSING})
    s = result.summaries["bad"]
    assert s.missing_in_target_count == 1


def test_summary_counts_for_extra_key():
    result = compare_many(SOURCE, {"extra": TARGET_EXTRA})
    s = result.summaries["extra"]
    assert s.missing_in_source_count == 1


def test_worst_target_returns_none_when_no_targets():
    result = CompareResult(source_name="src")
    assert result.worst_target() is None


def test_worst_target_identifies_most_issues():
    result = compare_many(
        SOURCE,
        {
            "ok": TARGET_OK,
            "bad": TARGET_MISSING,
            "worse": {"A": "X"},  # 2 missing + 1 mismatch
        },
    )
    worst = result.worst_target()
    assert worst == "worse"


def test_diff_result_statuses_present():
    result = compare_many(SOURCE, {"bad": TARGET_MISMATCH})
    statuses = {e.status for e in result.results["bad"].entries}
    assert DiffStatus.MISMATCH in statuses
