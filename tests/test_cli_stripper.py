"""Tests for envdiff.cli_stripper."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.cli_stripper import main


@pytest.fixture()
def source_file(tmp_path: Path) -> Path:
    p = tmp_path / "source.env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPP_ENV=prod\n")
    return p


@pytest.fixture()
def target_file(tmp_path: Path) -> Path:
    p = tmp_path / "target.env"
    p.write_text(
        "DB_HOST=remotehost\nDB_PORT=5432\nAPP_ENV=staging\nLEGACY_KEY=old\n"
    )
    return p


def test_main_returns_zero(source_file, target_file):
    assert main([str(source_file), str(target_file)]) == 0


def test_main_missing_source_returns_two(tmp_path, target_file):
    assert main([str(tmp_path / "nope.env"), str(target_file)]) == 2


def test_main_missing_target_returns_two(source_file, tmp_path):
    assert main([str(source_file), str(tmp_path / "nope.env")]) == 2


def test_main_json_output_is_valid_json(source_file, target_file, capsys):
    main([str(source_file), str(target_file), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "stripped_count" in data
    assert "output_env" in data


def test_main_json_stripped_count(source_file, target_file, capsys):
    main([str(source_file), str(target_file), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["stripped_count"] == 1


def test_main_json_output_env_excludes_stripped(source_file, target_file, capsys):
    main([str(source_file), str(target_file), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "LEGACY_KEY" not in data["output_env"]


def test_main_write_creates_file(source_file, target_file, tmp_path):
    out = tmp_path / "stripped.env"
    main([str(source_file), str(target_file), "--write", str(out)])
    assert out.exists()


def test_main_write_file_excludes_stripped_key(source_file, target_file, tmp_path):
    out = tmp_path / "stripped.env"
    main([str(source_file), str(target_file), "--write", str(out)])
    content = out.read_text()
    assert "LEGACY_KEY" not in content


def test_main_text_output_mentions_stripped(source_file, target_file, capsys):
    main([str(source_file), str(target_file)])
    out = capsys.readouterr().out
    assert "LEGACY_KEY" in out
