"""Tests for envdiff.cli_grouper."""

from __future__ import annotations

import pathlib

import pytest

from envdiff.cli_grouper import main


@pytest.fixture()
def env_source(tmp_path: pathlib.Path) -> pathlib.Path:
    p = tmp_path / "source.env"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "APP_DEBUG=true\n"
        "SECRET=abc\n"
    )
    return p


@pytest.fixture()
def env_target(tmp_path: pathlib.Path) -> pathlib.Path:
    p = tmp_path / "target.env"
    p.write_text(
        "DB_HOST=localhost\n"
        "APP_DEBUG=false\n"
        "APP_NAME=myapp\n"
    )
    return p


def test_main_returns_zero(env_source: pathlib.Path, env_target: pathlib.Path) -> None:
    code = main([str(env_source), str(env_target)])
    assert code == 0


def test_main_missing_source_returns_two(tmp_path: pathlib.Path, env_target: pathlib.Path) -> None:
    code = main([str(tmp_path / "missing.env"), str(env_target)])
    assert code == 2


def test_main_missing_target_returns_two(env_source: pathlib.Path, tmp_path: pathlib.Path) -> None:
    code = main([str(env_source), str(tmp_path / "missing.env")])
    assert code == 2


def test_main_output_contains_group_headers(
    env_source: pathlib.Path,
    env_target: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    main([str(env_source), str(env_target)])
    captured = capsys.readouterr()
    assert "[DB]" in captured.out
    assert "[APP]" in captured.out


def test_main_output_contains_source_and_target(
    env_source: pathlib.Path,
    env_target: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    main([str(env_source), str(env_target)])
    captured = capsys.readouterr()
    assert "source.env" in captured.out
    assert "target.env" in captured.out


def test_main_custom_separator(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    src = tmp_path / "s.env"
    tgt = tmp_path / "t.env"
    src.write_text("DB.HOST=localhost\n")
    tgt.write_text("DB.HOST=localhost\n")
    code = main([str(src), str(tgt), "--separator", "."])
    assert code == 0
    captured = capsys.readouterr()
    assert "[DB]" in captured.out


def test_main_custom_ungrouped_label(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    src = tmp_path / "s.env"
    tgt = tmp_path / "t.env"
    src.write_text("NOPREFIX=val\n")
    tgt.write_text("NOPREFIX=val\n")
    code = main([str(src), str(tgt), "--ungrouped-label", "MISC"])
    assert code == 0
    captured = capsys.readouterr()
    assert "[MISC]" in captured.out
