"""Tests for envdiff.statistics and envdiff.cli_statistics."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from envdiff.differ import DiffResult, DiffEntry, DiffStatus
from envdiff.statistics import EnvStatistics, compute_statistics
from envdiff.cli_statistics import main


def _entry(key: str, status: DiffStatus) -> DiffEntry:
    return DiffEntry(key=key, source_value="a", target_value="b", status=status)


def _result(*entries: DiffEntry) -> DiffResult:
    return DiffResult(source_name="src", target_name="tgt", entries=list(entries))


# ---------------------------------------------------------------------------
# compute_statistics
# ---------------------------------------------------------------------------

def test_compute_returns_env_statistics():
    stats = compute_statistics([])
    assert isinstance(stats, EnvStatistics)


def test_compute_empty_list():
    stats = compute_statistics([])
    assert stats.total_comparisons == 0
    assert stats.total_entries == 0
    assert stats.match_rate == 1.0


def test_compute_counts_comparisons():
    r1 = _result(_entry("A", DiffStatus.MATCH))
    r2 = _result(_entry("B", DiffStatus.MATCH))
    stats = compute_statistics([r1, r2])
    assert stats.total_comparisons == 2


def test_compute_total_entries():
    r = _result(
        _entry("A", DiffStatus.MATCH),
        _entry("B", DiffStatus.MISMATCH),
        _entry("C", DiffStatus.MISSING_IN_TARGET),
    )
    stats = compute_statistics([r])
    assert stats.total_entries == 3


def test_compute_match_count():
    r = _result(_entry("A", DiffStatus.MATCH), _entry("B", DiffStatus.MISMATCH))
    stats = compute_statistics([r])
    assert stats.total_matches == 1


def test_compute_mismatch_count():
    r = _result(_entry("A", DiffStatus.MISMATCH), _entry("B", DiffStatus.MISMATCH))
    stats = compute_statistics([r])
    assert stats.total_mismatches == 2


def test_compute_missing_in_target_count():
    r = _result(_entry("X", DiffStatus.MISSING_IN_TARGET))
    stats = compute_statistics([r])
    assert stats.total_missing_in_target == 1


def test_compute_missing_in_source_count():
    r = _result(_entry("Y", DiffStatus.MISSING_IN_SOURCE))
    stats = compute_statistics([r])
    assert stats.total_missing_in_source == 1


def test_compute_unique_keys_sorted():
    r = _result(_entry("ZEBRA", DiffStatus.MATCH), _entry("APPLE", DiffStatus.MATCH))
    stats = compute_statistics([r])
    assert stats.unique_keys == ["APPLE", "ZEBRA"]


def test_compute_unique_keys_deduplicated():
    r1 = _result(_entry("SHARED", DiffStatus.MATCH))
    r2 = _result(_entry("SHARED", DiffStatus.MISMATCH))
    stats = compute_statistics([r1, r2])
    assert stats.unique_keys == ["SHARED"]


def test_match_rate_all_match():
    r = _result(_entry("A", DiffStatus.MATCH), _entry("B", DiffStatus.MATCH))
    stats = compute_statistics([r])
    assert stats.match_rate == 1.0


def test_issue_rate_complement_of_match_rate():
    r = _result(_entry("A", DiffStatus.MATCH), _entry("B", DiffStatus.MISMATCH))
    stats = compute_statistics([r])
    assert abs(stats.match_rate + stats.issue_rate - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_source(tmp_path: Path) -> Path:
    p = tmp_path / "source.env"
    p.write_text(textwrap.dedent("""\
        KEY_A=hello
        KEY_B=world
    """))
    return p


@pytest.fixture()
def env_target(tmp_path: Path) -> Path:
    p = tmp_path / "target.env"
    p.write_text(textwrap.dedent("""\
        KEY_A=hello
        KEY_B=changed
    """))
    return p


def test_cli_returns_zero(env_source, env_target):
    assert main([str(env_source), str(env_target)]) == 0


def test_cli_missing_source_returns_two(tmp_path, env_target):
    assert main([str(tmp_path / "nope.env"), str(env_target)]) == 2


def test_cli_missing_target_returns_two(env_source, tmp_path):
    assert main([str(env_source), str(tmp_path / "nope.env")]) == 2


def test_cli_json_output_is_valid(env_source, env_target, capsys):
    main([str(env_source), str(env_target), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "total_comparisons" in data
    assert "match_rate" in data
    assert "unique_keys" in data


def test_cli_json_counts(env_source, env_target, capsys):
    main([str(env_source), str(env_target), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["total_comparisons"] == 1
    assert data["total_entries"] == 2
    assert data["total_matches"] == 1
    assert data["total_mismatches"] == 1
