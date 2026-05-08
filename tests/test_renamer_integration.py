"""Integration tests: rename keys then parse the output file back."""
from pathlib import Path

import pytest

from envdiff.parser import parse_env_file
from envdiff.renamer import rename_keys
from envdiff.cli_rename import main


@pytest.fixture()
def env_path(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "OLD_API_KEY=secret\nOLD_DB_URL=postgres://localhost/db\nSTABLE_KEY=unchanged\n",
        encoding="utf-8",
    )
    return p


def test_round_trip_rename_and_parse(env_path, tmp_path):
    """Rename keys, write output, parse it back and verify values are intact."""
    out = tmp_path / "renamed.env"
    env = parse_env_file(str(env_path))
    result = rename_keys(env, {"OLD_API_KEY": "API_KEY", "OLD_DB_URL": "DATABASE_URL"})
    lines = [f"{k}={v}" for k, v in result.renamed.items()]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    reparsed = parse_env_file(str(out))
    assert reparsed["API_KEY"] == "secret"
    assert reparsed["DATABASE_URL"] == "postgres://localhost/db"
    assert reparsed["STABLE_KEY"] == "unchanged"
    assert "OLD_API_KEY" not in reparsed
    assert "OLD_DB_URL" not in reparsed


def test_cli_round_trip(env_path, tmp_path):
    """CLI rename + parse back produces expected keys."""
    out = str(tmp_path / "out.env")
    rc = main([
        str(env_path),
        "OLD_API_KEY=API_KEY",
        "OLD_DB_URL=DATABASE_URL",
        "-o", out,
    ])
    assert rc == 0
    reparsed = parse_env_file(out)
    assert "API_KEY" in reparsed
    assert "DATABASE_URL" in reparsed


def test_partial_rename_missing_key_does_not_corrupt(env_path, tmp_path):
    """A missing source key should not affect other renames."""
    out = tmp_path / "out.env"
    env = parse_env_file(str(env_path))
    result = rename_keys(env, {"DOES_NOT_EXIST": "PHANTOM", "OLD_API_KEY": "API_KEY"})
    lines = [f"{k}={v}" for k, v in result.renamed.items()]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    reparsed = parse_env_file(str(out))
    assert "API_KEY" in reparsed
    assert "PHANTOM" not in reparsed
    assert result.skipped_count == 1
    assert result.applied_count == 1
