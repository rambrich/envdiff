"""Watch .env files for changes and report diffs on modification."""

from __future__ import annotations

import time
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from envdiff.parser import parse_env_file
from envdiff.differ import diff_envs, DiffResult


@dataclass
class WatchEvent:
    """Emitted when a watched file changes."""

    path: Path
    diff: DiffResult
    previous_mtime: float
    current_mtime: float

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"WatchEvent(path={self.path!r}, "
            f"has_issues={self.diff.has_issues()})"
        )


def _get_mtime(path: Path) -> float:
    """Return the modification time of *path*, or 0.0 if it does not exist."""
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def watch(
    source: Path,
    target: Path,
    callback: Callable[[WatchEvent], None],
    *,
    interval: float = 1.0,
    max_events: Optional[int] = None,
) -> None:
    """Poll *source* and *target* for changes and invoke *callback* on each change.

    Parameters
    ----------
    source:
        The reference .env file.
    target:
        The .env file being watched for changes.
    callback:
        Called with a :class:`WatchEvent` whenever *target* (or *source*) changes.
    interval:
        Polling interval in seconds.
    max_events:
        Stop after this many events (useful for testing). ``None`` means run forever.
    """
    source = Path(source)
    target = Path(target)

    last_source_mtime = _get_mtime(source)
    last_target_mtime = _get_mtime(target)

    events_emitted = 0

    while True:
        if max_events is not None and events_emitted >= max_events:
            break

        time.sleep(interval)

        current_source_mtime = _get_mtime(source)
        current_target_mtime = _get_mtime(target)

        changed = (
            current_source_mtime != last_source_mtime
            or current_target_mtime != last_target_mtime
        )

        if changed:
            source_env = parse_env_file(source)
            target_env = parse_env_file(target)
            result = diff_envs(source_env, target_env, source_name=str(source), target_name=str(target))

            event = WatchEvent(
                path=target,
                diff=result,
                previous_mtime=last_target_mtime,
                current_mtime=current_target_mtime,
            )
            callback(event)
            events_emitted += 1

            last_source_mtime = current_source_mtime
            last_target_mtime = current_target_mtime
