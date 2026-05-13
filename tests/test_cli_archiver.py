"""Tests for envdiff.cli_archiver."""
from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from envdiff.cli_archiver import main


@pytest.fixture()
def env_file(tmp_path: Path) -> str:
    p = tmp_path / "sample.env"
    p.write_text("KEY=value\nOTHER=123\n")
    return str(p)


@pytest.fixture()
def env_file2(tmp_path: Path) -> str:
    p = tmp_path / "other.env"
    p.write_text("ALPHA=a\nBETA=b\n")
    return str(p)


@pytest.fixture()
def archive_zip(tmp_path: Path, env_file: str, env_file2: str) -> str:
    out = str(tmp_path / "archive.zip")
    main(["create", env_file, env_file2, "--output", out])
    return out


def test_create_returns_zero(tmp_path, env_file, env_file2):
    out = str(tmp_path / "test.zip")
    code = main(["create", env_file, env_file2, "--output", out])
    assert code == 0


def test_create_produces_zip_file(archive_zip):
    assert zipfile.is_zipfile(archive_zip)


def test_list_returns_zero(archive_zip):
    code = main(["list", archive_zip])
    assert code == 0


def test_list_missing_archive_returns_two(tmp_path):
    missing = str(tmp_path / "no_such.zip")
    code = main(["list", missing])
    assert code == 2


def test_list_output_contains_snapshot_names(archive_zip, capsys):
    main(["list", archive_zip])
    captured = capsys.readouterr().out
    assert "sample" in captured or "other" in captured


def test_create_output_mentions_archive_path(tmp_path, env_file, capsys):
    out = str(tmp_path / "mention.zip")
    main(["create", env_file, "--output", out])
    captured = capsys.readouterr().out
    assert "mention.zip" in captured


def test_create_single_env_snapshot_count(tmp_path, env_file, capsys):
    out = str(tmp_path / "single.zip")
    main(["create", env_file, "--output", out])
    captured = capsys.readouterr().out
    assert "1" in captured
