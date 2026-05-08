"""Tests for envdiff.cli_rename."""
import json
from pathlib import Path

import pytest

from envdiff.cli_rename import main


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPP_SECRET=abc\n", encoding="utf-8")
    return str(p)


def test_main_returns_zero(env_file):
    rc = main([env_file, "DB_HOST=DATABASE_HOST"])
    assert rc == 0


def test_main_invalid_pair_returns_two(env_file):
    rc = main([env_file, "BADPAIR"])
    assert rc == 2


def test_main_json_output_is_valid_json(env_file, capsys):
    main([env_file, "DB_HOST=DATABASE_HOST", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "renamed" in data
    assert "records" in data


def test_main_json_renamed_contains_new_key(env_file, capsys):
    main([env_file, "DB_HOST=DATABASE_HOST", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "DATABASE_HOST" in data["renamed"]


def test_main_json_old_key_removed_by_default(env_file, capsys):
    main([env_file, "DB_HOST=DATABASE_HOST", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "DB_HOST" not in data["renamed"]


def test_main_keep_old_flag(env_file, capsys):
    main([env_file, "DB_HOST=DATABASE_HOST", "--keep-old", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "DB_HOST" in data["renamed"]
    assert "DATABASE_HOST" in data["renamed"]


def test_main_output_file_written(env_file, tmp_path):
    out = str(tmp_path / "out.env")
    main([env_file, "DB_HOST=DATABASE_HOST", "-o", out])
    content = Path(out).read_text(encoding="utf-8")
    assert "DATABASE_HOST=localhost" in content


def test_main_output_file_no_old_key(env_file, tmp_path):
    out = str(tmp_path / "out.env")
    main([env_file, "DB_HOST=DATABASE_HOST", "-o", out])
    content = Path(out).read_text(encoding="utf-8")
    assert "DB_HOST=" not in content


def test_main_text_output_shows_ok(env_file, capsys):
    main([env_file, "DB_HOST=DATABASE_HOST"])
    out = capsys.readouterr().out
    assert "[OK]" in out


def test_main_text_output_shows_skip_for_missing(env_file, capsys):
    main([env_file, "MISSING_KEY=NEW_KEY"])
    out = capsys.readouterr().out
    assert "[SKIP]" in out
