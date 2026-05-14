"""Tests for envdiff.scorer_matrix and envdiff.cli_scorer_matrix."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.differ import DiffStatus
from envdiff.differ_matrix import build_matrix
from envdiff.scorer_matrix import MatrixScoreEntry, MatrixScoreResult, score_matrix


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def source() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc"}


@pytest.fixture()
def targets(source) -> list[dict]:
    perfect = dict(source)
    partial = {"DB_HOST": "localhost", "DB_PORT": "9999"}  # mismatch + missing
    empty: dict = {}
    return [perfect, partial, empty]


@pytest.fixture()
def matrix(source, targets):
    src = {"name": "source", **source}
    tgts = [
        {"name": f"target_{i}", **t} for i, t in enumerate(targets)
    ]
    # Build using raw dicts via build_matrix helper
    source_env = type("E", (), {"name": "source", "keys": lambda s: source.keys(), "__iter__": lambda s: iter(source.items())})()
    # Use simpler approach: build_matrix expects parsed env dicts
    from envdiff.differ_matrix import build_matrix as _bm
    from envdiff.differ import diff

    class FakeEnv(dict):
        def __init__(self, name, data):
            super().__init__(data)
            self.name = name

    src_env = FakeEnv("source", source)
    tgt_envs = [FakeEnv(f"target_{i}", t) for i, t in enumerate(targets)]
    return _bm(src_env, tgt_envs)


# ---------------------------------------------------------------------------
# score_matrix unit tests
# ---------------------------------------------------------------------------

def test_score_matrix_returns_matrix_score_result(matrix):
    result = score_matrix(matrix)
    assert isinstance(result, MatrixScoreResult)


def test_score_matrix_source_name_stored(matrix):
    result = score_matrix(matrix)
    assert result.source_name == "source"


def test_score_matrix_entry_count_matches_targets(matrix):
    result = score_matrix(matrix)
    assert len(result.entries) == 3


def test_score_matrix_entries_are_matrix_score_entries(matrix):
    result = score_matrix(matrix)
    for entry in result.entries:
        assert isinstance(entry, MatrixScoreEntry)


def test_score_matrix_perfect_target_scores_100(matrix):
    result = score_matrix(matrix)
    perfect = next(e for e in result.entries if e.target_name == "target_0")
    assert perfect.score.score == 100.0


def test_score_matrix_empty_target_scores_zero(matrix):
    result = score_matrix(matrix)
    empty = next(e for e in result.entries if e.target_name == "target_2")
    assert empty.score.score == 0.0


def test_score_matrix_average_between_zero_and_100(matrix):
    result = score_matrix(matrix)
    assert 0.0 <= result.average_score <= 100.0


def test_score_matrix_lowest_entry_has_minimum_score(matrix):
    result = score_matrix(matrix)
    lowest = result.lowest_entry
    assert lowest is not None
    assert all(lowest.score.score <= e.score.score for e in result.entries)


def test_score_matrix_highest_entry_has_maximum_score(matrix):
    result = score_matrix(matrix)
    highest = result.highest_entry
    assert highest is not None
    assert all(highest.score.score >= e.score.score for e in result.entries)


def test_score_matrix_empty_matrix_average_is_100():
    from envdiff.differ_matrix import DiffMatrix
    empty_matrix = DiffMatrix(source_name="src", cells=[])
    result = score_matrix(empty_matrix)
    assert result.average_score == 100.0
    assert result.lowest_entry is None
    assert result.highest_entry is None


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def source_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env.source"
    f.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc\n")
    return f


@pytest.fixture()
def perfect_target(tmp_path: Path) -> Path:
    f = tmp_path / ".env.perfect"
    f.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc\n")
    return f


@pytest.fixture()
def bad_target(tmp_path: Path) -> Path:
    f = tmp_path / ".env.bad"
    f.write_text("DB_HOST=other\n")
    return f


def test_cli_returns_zero(source_file, perfect_target, bad_target):
    from envdiff.cli_scorer_matrix import main
    rc = main([str(source_file), str(perfect_target), str(bad_target)])
    assert rc == 0


def test_cli_missing_source_returns_two(tmp_path, perfect_target):
    from envdiff.cli_scorer_matrix import main
    rc = main([str(tmp_path / "nope.env"), str(perfect_target)])
    assert rc == 2


def test_cli_missing_target_returns_two(source_file, tmp_path):
    from envdiff.cli_scorer_matrix import main
    rc = main([str(source_file), str(tmp_path / "nope.env")])
    assert rc == 2


def test_cli_json_output_is_valid(source_file, perfect_target, bad_target, capsys):
    from envdiff.cli_scorer_matrix import main
    main(["--json", str(source_file), str(perfect_target), str(bad_target)])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "source" in data
    assert "average_score" in data
    assert isinstance(data["targets"], list)


def test_cli_json_contains_grade(source_file, perfect_target, capsys):
    from envdiff.cli_scorer_matrix import main
    main(["--json", str(source_file), str(perfect_target)])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "grade" in data["targets"][0]
