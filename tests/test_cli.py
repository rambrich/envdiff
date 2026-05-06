"""Tests for the envdiff CLI module."""

import pytest
from pathlib import Path

from envdiff.cli import main, build_parser


@pytest.fixture
def env_source(tmp_path: Path) -> Path:
    p = tmp_path / ".env.example"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=changeme\n")
    return p


@pytest.fixture
def env_target(tmp_path: Path) -> Path:
    p = tmp_path / ".env.production"
    p.write_text("DB_HOST=prod-db.example.com\nDB_PORT=5432\n")
    return p


def test_main_returns_zero_no_issues(tmp_path: Path) -> None:
    src = tmp_path / "a.env"
    tgt = tmp_path / "b.env"
    src.write_text("FOO=bar\n")
    tgt.write_text("FOO=bar\n")
    assert main([str(src), str(tgt)]) == 0


def test_main_returns_zero_with_issues_no_exit_code_flag(
    env_source: Path, env_target: Path
) -> None:
    assert main([str(env_source), str(env_target)]) == 0


def test_main_returns_one_with_issues_and_exit_code_flag(
    env_source: Path, env_target: Path
) -> None:
    assert main([str(env_source), str(env_target), "--exit-code"]) == 1


def test_main_missing_source_returns_2(tmp_path: Path) -> None:
    tgt = tmp_path / "b.env"
    tgt.write_text("FOO=bar\n")
    assert main([str(tmp_path / "nonexistent.env"), str(tgt)]) == 2


def test_main_missing_target_returns_2(tmp_path: Path) -> None:
    src = tmp_path / "a.env"
    src.write_text("FOO=bar\n")
    assert main([str(src), str(tmp_path / "nonexistent.env")]) == 2


def test_main_no_values_flag_does_not_crash(
    env_source: Path, env_target: Path
) -> None:
    assert main([str(env_source), str(env_target), "--no-values"]) == 0


def test_build_parser_prog_name() -> None:
    parser = build_parser()
    assert parser.prog == "envdiff"


def test_build_parser_defaults() -> None:
    parser = build_parser()
    args = parser.parse_args(["src.env", "tgt.env"])
    assert args.no_values is False
    assert args.exit_code is False
