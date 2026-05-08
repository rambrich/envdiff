"""Snapshot an env file at a point in time for later comparison."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Optional

from envdiff.parser import parse_env_file


@dataclass
class EnvSnapshot:
    """Represents a captured snapshot of an env file."""

    name: str
    captured_at: float
    env: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EnvSnapshot":
        return cls(
            name=data["name"],
            captured_at=data["captured_at"],
            env=data.get("env", {}),
        )

    def key_count(self) -> int:
        return len(self.env)


def capture_snapshot(
    path: str | Path,
    name: Optional[str] = None,
) -> EnvSnapshot:
    """Parse an env file and wrap it in a timestamped snapshot."""
    path = Path(path)
    env = parse_env_file(path)
    return EnvSnapshot(
        name=name or path.name,
        captured_at=time.time(),
        env=env,
    )


def save_snapshot(snapshot: EnvSnapshot, dest: str | Path) -> None:
    """Persist a snapshot to a JSON file."""
    dest = Path(dest)
    dest.write_text(json.dumps(snapshot.to_dict(), indent=2))


def load_snapshot(src: str | Path) -> EnvSnapshot:
    """Load a snapshot from a JSON file."""
    src = Path(src)
    data = json.loads(src.read_text())
    return EnvSnapshot.from_dict(data)


def diff_snapshots(
    old: EnvSnapshot, new: EnvSnapshot
) -> Dict[str, tuple]:
    """Return keys that changed between two snapshots.

    Returns a dict mapping key -> (old_value, new_value).
    A value of None means the key was absent.
    """
    all_keys = set(old.env) | set(new.env)
    changes: Dict[str, tuple] = {}
    for key in sorted(all_keys):
        old_val = old.env.get(key)
        new_val = new.env.get(key)
        if old_val != new_val:
            changes[key] = (old_val, new_val)
    return changes
