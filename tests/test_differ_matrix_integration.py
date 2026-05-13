"""Integration tests: parse real files then build a matrix."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.differ_matrix import build_matrix
from envdiff.parser import parse_env_file


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    (tmp_path / ".env").write_text(
        "APP_NAME=myapp\nDEBUG=true\nDB_URL=postgres://localhost/dev\n"
    )
    (tmp_path / ".env.staging").write_text(
        "APP_NAME=myapp\nDEBUG=false\nDB_URL=postgres://staging/db\n"
    )
    (tmp_path / ".env.prod").write_text(
        "APP_NAME=myapp\nDB_URL=postgres://prod/db\n"  # missing DEBUG
    )
    return tmp_path


def test_integration_matrix_cell_count(env_dir):
    source = parse_env_file(env_dir / ".env")
    targets = {
        "staging": parse_env_file(env_dir / ".env.staging"),
        "prod": parse_env_file(env_dir / ".env.prod"),
    }
    matrix = build_matrix(source, targets, source_name=".env")
    assert len(matrix.cells) == 2


def test_integration_prod_has_issues(env_dir):
    source = parse_env_file(env_dir / ".env")
    targets = {
        "staging": parse_env_file(env_dir / ".env.staging"),
        "prod": parse_env_file(env_dir / ".env.prod"),
    }
    matrix = build_matrix(source, targets, source_name=".env")
    assert "prod" in matrix.failing_targets


def test_integration_staging_has_issues(env_dir):
    source = parse_env_file(env_dir / ".env")
    targets = {
        "staging": parse_env_file(env_dir / ".env.staging"),
    }
    matrix = build_matrix(source, targets, source_name=".env")
    # DEBUG and DB_URL differ → staging has issues
    assert "staging" in matrix.failing_targets


def test_integration_get_result_entries(env_dir):
    source = parse_env_file(env_dir / ".env")
    targets = {"prod": parse_env_file(env_dir / ".env.prod")}
    matrix = build_matrix(source, targets, source_name=".env")
    result = matrix.get("prod")
    keys = {e.key for e in result.entries}
    assert "DEBUG" in keys
