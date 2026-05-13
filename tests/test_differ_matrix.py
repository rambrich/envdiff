"""Unit tests for envdiff.differ_matrix."""
from __future__ import annotations

import pytest

from envdiff.differ_matrix import DiffMatrix, MatrixCell, build_matrix


@pytest.fixture()
def source() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc"}


@pytest.fixture()
def targets(source) -> dict:
    return {
        "staging": {"DB_HOST": "staging-host", "DB_PORT": "5432", "SECRET": "abc"},
        "prod": {"DB_HOST": "prod-host", "DB_PORT": "5432"},  # missing SECRET
        "local": dict(source),  # perfect match
    }


@pytest.fixture()
def matrix(source, targets) -> DiffMatrix:
    return build_matrix(source, targets, source_name=".env")


def test_build_matrix_returns_diff_matrix(matrix):
    assert isinstance(matrix, DiffMatrix)


def test_build_matrix_source_name(matrix):
    assert matrix.source_name == ".env"


def test_build_matrix_cell_count(matrix, targets):
    assert len(matrix.cells) == len(targets)


def test_build_matrix_target_names(matrix, targets):
    assert set(matrix.target_names) == set(targets.keys())


def test_matrix_has_any_issues_true(matrix):
    assert matrix.has_any_issues is True


def test_matrix_clean_targets_contains_local(matrix):
    assert "local" in matrix.clean_targets


def test_matrix_failing_targets_contains_prod(matrix):
    assert "prod" in matrix.failing_targets


def test_matrix_failing_targets_contains_staging(matrix):
    assert "staging" in matrix.failing_targets


def test_matrix_get_returns_diff_result(matrix):
    result = matrix.get("local")
    assert result is not None
    assert not result.has_issues


def test_matrix_get_unknown_returns_none(matrix):
    assert matrix.get("nonexistent") is None


def test_matrix_cell_has_issues_false_for_clean(matrix):
    local_cell = next(c for c in matrix.cells if c.target_name == "local")
    assert local_cell.has_issues is False


def test_build_matrix_empty_targets(source):
    matrix = build_matrix(source, {})
    assert matrix.cells == []
    assert not matrix.has_any_issues
