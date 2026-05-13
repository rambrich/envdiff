"""Tests for envdiff.cli_matrix."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.cli_matrix import main


@pytest.fixture()
def source_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc\n")
    return f


@pytest.fixture()
def matching_target(tmp_path: Path) -> Path:
    f = tmp_path / ".env.local"
    f.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc\n")
    return f


@pytest.fixture()
def mismatched_target(tmp_path: Path) -> Path:
    f = tmp_path / ".env.prod"
    f.write_text("DB_HOST=prod-host\nDB_PORT=5432\n")
    return f


def test_main_returns_zero_no_issues(source_file, matching_target):
    code = main([str(source_file), str(matching_target)])
    assert code == 0


def test_main_returns_zero_with_issues_no_exit_code_flag(source_file, mismatched_target):
    code = main([str(source_file), str(mismatched_target)])
    assert code == 0


def test_main_returns_one_with_issues_and_exit_code_flag(source_file, mismatched_target):
    code = main([str(source_file), str(mismatched_target), "--exit-code"])
    assert code == 1


def test_main_missing_source_returns_two(tmp_path, matching_target):
    code = main([str(tmp_path / "missing.env"), str(matching_target)])
    assert code == 2


def test_main_missing_target_returns_two(source_file, tmp_path):
    code = main([str(source_file), str(tmp_path / "missing.env")])
    assert code == 2


def test_main_json_output_is_valid(source_file, matching_target, capsys):
    main([str(source_file), str(matching_target), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "source" in data
    assert "targets" in data


def test_main_json_target_entry_has_name(source_file, matching_target, capsys):
    main([str(source_file), str(matching_target), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["targets"][0]["name"] == matching_target.name


def test_main_text_output_contains_header(source_file, matching_target, capsys):
    main([str(source_file), str(matching_target)])
    captured = capsys.readouterr()
    assert "Matrix:" in captured.out


def test_main_multiple_targets(source_file, matching_target, mismatched_target, capsys):
    main([str(source_file), str(matching_target), str(mismatched_target)])
    captured = capsys.readouterr()
    assert matching_target.name in captured.out
    assert mismatched_target.name in captured.out
