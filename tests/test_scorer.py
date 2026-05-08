"""Tests for envdiff.scorer and envdiff.cli_score."""
from __future__ import annotations

import pytest

from envdiff.differ import DiffResult, DiffEntry, DiffStatus
from envdiff.scorer import score_diff, DiffScore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(key: str, status: DiffStatus) -> DiffEntry:
    src = "a" if status != DiffStatus.MISSING_IN_SOURCE else None
    tgt = "b" if status != DiffStatus.MISSING_IN_TARGET else None
    if status == DiffStatus.MATCH:
        src = tgt = "same"
    return DiffEntry(key=key, source_value=src, target_value=tgt, status=status)


def _result(*entries: DiffEntry) -> DiffResult:
    return DiffResult(source="src", target="tgt", entries=list(entries))


# ---------------------------------------------------------------------------
# score_diff
# ---------------------------------------------------------------------------

def test_score_returns_diff_score():
    r = _result(_entry("K", DiffStatus.MATCH))
    assert isinstance(score_diff(r), DiffScore)


def test_score_all_matches_is_100():
    r = _result(
        _entry("A", DiffStatus.MATCH),
        _entry("B", DiffStatus.MATCH),
    )
    ds = score_diff(r)
    assert ds.score == 100.0


def test_score_empty_result_is_100():
    r = DiffResult(source="s", target="t", entries=[])
    ds = score_diff(r)
    assert ds.score == 100.0
    assert ds.total_keys == 0


def test_score_all_missing_in_target_is_0():
    r = _result(
        _entry("A", DiffStatus.MISSING_IN_TARGET),
        _entry("B", DiffStatus.MISSING_IN_TARGET),
    )
    ds = score_diff(r)
    assert ds.score == 0.0


def test_score_mismatch_weight_applied():
    # 2 keys: 1 match + 1 mismatch with default weight 0.5
    # penalty = 0.5, score = (2 - 0.5) / 2 * 100 = 75.0
    r = _result(_entry("A", DiffStatus.MATCH), _entry("B", DiffStatus.MISMATCH))
    ds = score_diff(r)
    assert ds.score == 75.0


def test_score_custom_mismatch_weight():
    r = _result(_entry("A", DiffStatus.MATCH), _entry("B", DiffStatus.MISMATCH))
    ds = score_diff(r, mismatch_weight=1.0)
    assert ds.score == 50.0


def test_score_counts_are_correct():
    r = _result(
        _entry("A", DiffStatus.MATCH),
        _entry("B", DiffStatus.MISSING_IN_TARGET),
        _entry("C", DiffStatus.MISSING_IN_SOURCE),
        _entry("D", DiffStatus.MISMATCH),
    )
    ds = score_diff(r)
    assert ds.match_count == 1
    assert ds.missing_in_target_count == 1
    assert ds.missing_in_source_count == 1
    assert ds.mismatch_count == 1
    assert ds.total_keys == 4


def test_grade_A():
    r = _result(_entry("K", DiffStatus.MATCH))
    assert score_diff(r).grade == "A"


def test_grade_F():
    r = _result(_entry("K", DiffStatus.MISSING_IN_TARGET))
    assert score_diff(r).grade == "F"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_main_exits_zero_on_perfect_score(tmp_path):
    from envdiff.cli_score import main

    env = tmp_path / "a.env"
    env.write_text("FOO=bar\nBAZ=qux\n")
    ret = main([str(env), str(env)])
    assert ret == 0


def test_cli_main_exits_one_when_below_min_score(tmp_path):
    from envdiff.cli_score import main

    src = tmp_path / "src.env"
    tgt = tmp_path / "tgt.env"
    src.write_text("FOO=bar\nMISSING=yes\n")
    tgt.write_text("FOO=bar\n")
    ret = main([str(src), str(tgt), "--min-score", "100"])
    assert ret == 1


def test_cli_main_exits_zero_above_min_score(tmp_path):
    from envdiff.cli_score import main

    env = tmp_path / "a.env"
    env.write_text("FOO=bar\n")
    ret = main([str(env), str(env), "--min-score", "50"])
    assert ret == 0
