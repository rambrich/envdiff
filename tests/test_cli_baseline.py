"""Tests for envdiff.cli_baseline module."""

import json
import pytest
from pathlib import Path

from envdiff.cli_baseline import main


@pytest.fixture
def env_file(tmp_path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc\n", encoding="utf-8")
    return p


@pytest.fixture
def baseline_json(tmp_path, env_file) -> Path:
    out = tmp_path / "baseline.json"
    main(["baseline-save", str(env_file), "--name", "prod", "--output", str(out)])
    return out


# ---------------------------------------------------------------------------
# baseline-save
# ---------------------------------------------------------------------------

def test_save_creates_file(tmp_path, env_file):
    out = tmp_path / "snap.json"
    rc = main(["baseline-save", str(env_file), "--name", "prod", "--output", str(out)])
    assert rc == 0
    assert out.exists()


def test_save_json_contains_name(tmp_path, env_file):
    out = tmp_path / "snap.json"
    main(["baseline-save", str(env_file), "--name", "staging", "--output", str(out)])
    data = json.loads(out.read_text())
    assert data["name"] == "staging"


def test_save_json_contains_env_keys(tmp_path, env_file):
    out = tmp_path / "snap.json"
    main(["baseline-save", str(env_file), "--name", "prod", "--output", str(out)])
    data = json.loads(out.read_text())
    assert "DB_HOST" in data["env"]
    assert "DB_PORT" in data["env"]


def test_save_with_description(tmp_path, env_file):
    out = tmp_path / "snap.json"
    main(["baseline-save", str(env_file), "--name", "prod",
          "--output", str(out), "--description", "nightly"])
    data = json.loads(out.read_text())
    assert data["description"] == "nightly"


# ---------------------------------------------------------------------------
# baseline-compare
# ---------------------------------------------------------------------------

def test_compare_returns_zero_when_identical(baseline_json, env_file):
    rc = main(["baseline-compare", str(baseline_json), str(env_file)])
    assert rc == 0


def test_compare_returns_zero_with_issues_no_flag(tmp_path, baseline_json):
    diff_env = tmp_path / "diff.env"
    diff_env.write_text("DB_HOST=remotehost\n", encoding="utf-8")
    rc = main(["baseline-compare", str(baseline_json), str(diff_env)])
    assert rc == 0


def test_compare_returns_one_with_issues_and_flag(tmp_path, baseline_json):
    diff_env = tmp_path / "diff.env"
    diff_env.write_text("DB_HOST=remotehost\n", encoding="utf-8")
    rc = main(["baseline-compare", str(baseline_json), str(diff_env), "--exit-code"])
    assert rc == 1


def test_compare_custom_name(capsys, baseline_json, env_file):
    main(["baseline-compare", str(baseline_json), str(env_file), "--name", "local"])
    out = capsys.readouterr().out
    assert "local" in out


def test_no_subcommand_returns_zero():
    rc = main([])
    assert rc == 0
