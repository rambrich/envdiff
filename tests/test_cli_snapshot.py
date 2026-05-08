"""Tests for envdiff.cli_snapshot."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.cli_snapshot import main
from envdiff.snapshotter import EnvSnapshot, save_snapshot


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("ALPHA=1\nBETA=2\n")
    return p


@pytest.fixture()
def old_snap(tmp_path: Path) -> Path:
    snap = EnvSnapshot("old", 0.0, {"KEY": "original"})
    dest = tmp_path / "old.json"
    save_snapshot(snap, dest)
    return dest


@pytest.fixture()
def new_snap(tmp_path: Path) -> Path:
    snap = EnvSnapshot("new", 1.0, {"KEY": "changed", "EXTRA": "added"})
    dest = tmp_path / "new.json"
    save_snapshot(snap, dest)
    return dest


# --- capture command ---

def test_capture_creates_output_file(env_file, tmp_path):
    out = tmp_path / "out.json"
    rc = main(["capture", str(env_file), "--output", str(out)])
    assert rc == 0
    assert out.exists()


def test_capture_output_is_valid_json(env_file, tmp_path):
    out = tmp_path / "out.json"
    main(["capture", str(env_file), "--output", str(out)])
    data = json.loads(out.read_text())
    assert "env" in data
    assert data["env"]["ALPHA"] == "1"


def test_capture_custom_name_stored(env_file, tmp_path):
    out = tmp_path / "out.json"
    main(["capture", str(env_file), "--name", "staging", "--output", str(out)])
    data = json.loads(out.read_text())
    assert data["name"] == "staging"


def test_capture_returns_zero(env_file, tmp_path):
    out = tmp_path / "out.json"
    rc = main(["capture", str(env_file), "--output", str(out)])
    assert rc == 0


# --- diff command ---

def test_diff_no_changes_returns_zero(tmp_path):
    snap = EnvSnapshot("s", 0.0, {"X": "1"})
    p1 = tmp_path / "a.json"
    p2 = tmp_path / "b.json"
    save_snapshot(snap, p1)
    save_snapshot(snap, p2)
    rc = main(["diff", str(p1), str(p2)])
    assert rc == 0


def test_diff_with_changes_returns_zero_without_flag(old_snap, new_snap):
    rc = main(["diff", str(old_snap), str(new_snap)])
    assert rc == 0


def test_diff_with_changes_returns_one_with_exit_code_flag(old_snap, new_snap):
    rc = main(["diff", str(old_snap), str(new_snap), "--exit-code"])
    assert rc == 1


def test_diff_output_mentions_changed_key(old_snap, new_snap, capsys):
    main(["diff", str(old_snap), str(new_snap)])
    out = capsys.readouterr().out
    assert "KEY" in out


def test_diff_output_shows_added_key(old_snap, new_snap, capsys):
    main(["diff", str(old_snap), str(new_snap)])
    out = capsys.readouterr().out
    assert "EXTRA" in out
    assert "added" in out
