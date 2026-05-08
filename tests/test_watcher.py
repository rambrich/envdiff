"""Tests for envdiff.watcher."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envdiff.watcher import watch, WatchEvent, _get_mtime


@pytest.fixture()
def env_source(tmp_path: Path) -> Path:
    p = tmp_path / "source.env"
    p.write_text("KEY_A=hello\nKEY_B=world\n")
    return p


@pytest.fixture()
def env_target(tmp_path: Path) -> Path:
    p = tmp_path / "target.env"
    p.write_text("KEY_A=hello\nKEY_B=world\n")
    return p


def _touch(path: Path, content: str) -> None:
    """Write *content* to *path* and bump its mtime slightly."""
    path.write_text(content)
    # Ensure mtime differs from the previous value on fast file systems.
    current = path.stat().st_mtime
    new_mtime = current + 1.0
    import os
    os.utime(path, (new_mtime, new_mtime))


def test_get_mtime_returns_float(env_source: Path) -> None:
    mtime = _get_mtime(env_source)
    assert isinstance(mtime, float)
    assert mtime > 0


def test_get_mtime_missing_file_returns_zero(tmp_path: Path) -> None:
    assert _get_mtime(tmp_path / "nonexistent.env") == 0.0


def test_watch_detects_target_change(env_source: Path, env_target: Path) -> None:
    events: list[WatchEvent] = []

    def _cb(ev: WatchEvent) -> None:
        events.append(ev)

    # Modify target before the first poll tick.
    _touch(env_target, "KEY_A=hello\nKEY_B=changed\n")

    watch(env_source, env_target, _cb, interval=0.05, max_events=1)

    assert len(events) == 1
    assert events[0].path == env_target
    assert events[0].diff.has_issues()


def test_watch_event_no_issues_when_identical(env_source: Path, env_target: Path) -> None:
    events: list[WatchEvent] = []

    _touch(env_target, "KEY_A=hello\nKEY_B=world\n")

    watch(env_source, env_target, events.append, interval=0.05, max_events=1)

    assert len(events) == 1
    assert not events[0].diff.has_issues()


def test_watch_event_stores_mtime(env_source: Path, env_target: Path) -> None:
    events: list[WatchEvent] = []

    old_mtime = _get_mtime(env_target)
    _touch(env_target, "KEY_A=new\n")

    watch(env_source, env_target, events.append, interval=0.05, max_events=1)

    ev = events[0]
    assert ev.previous_mtime == old_mtime
    assert ev.current_mtime > old_mtime


def test_watch_repr(env_source: Path, env_target: Path) -> None:
    events: list[WatchEvent] = []
    _touch(env_target, "KEY_A=hello\n")
    watch(env_source, env_target, events.append, interval=0.05, max_events=1)
    r = repr(events[0])
    assert "WatchEvent" in r
    assert "has_issues" in r
