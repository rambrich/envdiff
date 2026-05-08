"""Tests for envdiff.snapshotter."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envdiff.snapshotter import (
    EnvSnapshot,
    capture_snapshot,
    save_snapshot,
    load_snapshot,
    diff_snapshots,
)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return p


# --- EnvSnapshot dataclass ---

def test_snapshot_key_count():
    snap = EnvSnapshot(name="test", captured_at=0.0, env={"A": "1", "B": "2"})
    assert snap.key_count() == 2


def test_snapshot_to_dict_round_trip():
    snap = EnvSnapshot(name="x", captured_at=1.0, env={"K": "V"})
    d = snap.to_dict()
    restored = EnvSnapshot.from_dict(d)
    assert restored.name == snap.name
    assert restored.captured_at == snap.captured_at
    assert restored.env == snap.env


# --- capture_snapshot ---

def test_capture_snapshot_reads_env(env_file):
    snap = capture_snapshot(env_file)
    assert snap.env["FOO"] == "bar"
    assert snap.env["BAZ"] == "qux"


def test_capture_snapshot_default_name(env_file):
    snap = capture_snapshot(env_file)
    assert snap.name == env_file.name


def test_capture_snapshot_custom_name(env_file):
    snap = capture_snapshot(env_file, name="production")
    assert snap.name == "production"


def test_capture_snapshot_timestamp_is_recent(env_file):
    before = time.time()
    snap = capture_snapshot(env_file)
    after = time.time()
    assert before <= snap.captured_at <= after


# --- save / load ---

def test_save_and_load_round_trip(env_file, tmp_path):
    snap = capture_snapshot(env_file)
    dest = tmp_path / "snap.json"
    save_snapshot(snap, dest)
    loaded = load_snapshot(dest)
    assert loaded.name == snap.name
    assert loaded.env == snap.env


def test_save_produces_valid_json(env_file, tmp_path):
    snap = capture_snapshot(env_file)
    dest = tmp_path / "snap.json"
    save_snapshot(snap, dest)
    data = json.loads(dest.read_text())
    assert "env" in data
    assert "captured_at" in data


# --- diff_snapshots ---

def test_diff_snapshots_no_changes():
    old = EnvSnapshot("a", 0.0, {"X": "1"})
    new = EnvSnapshot("b", 1.0, {"X": "1"})
    assert diff_snapshots(old, new) == {}


def test_diff_snapshots_added_key():
    old = EnvSnapshot("a", 0.0, {})
    new = EnvSnapshot("b", 1.0, {"NEW": "val"})
    changes = diff_snapshots(old, new)
    assert "NEW" in changes
    assert changes["NEW"] == (None, "val")


def test_diff_snapshots_removed_key():
    old = EnvSnapshot("a", 0.0, {"GONE": "bye"})
    new = EnvSnapshot("b", 1.0, {})
    changes = diff_snapshots(old, new)
    assert changes["GONE"] == ("bye", None)


def test_diff_snapshots_changed_value():
    old = EnvSnapshot("a", 0.0, {"K": "old"})
    new = EnvSnapshot("b", 1.0, {"K": "new"})
    changes = diff_snapshots(old, new)
    assert changes["K"] == ("old", "new")


def test_diff_snapshots_keys_sorted():
    old = EnvSnapshot("a", 0.0, {"Z": "1", "A": "x"})
    new = EnvSnapshot("b", 1.0, {"Z": "2", "A": "y"})
    keys = list(diff_snapshots(old, new).keys())
    assert keys == sorted(keys)
