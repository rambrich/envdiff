"""Track key changes between two versions of an env dict over time."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class TrackedChange:
    key: str
    change_type: ChangeType
    old_value: Optional[str]
    new_value: Optional[str]

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"TrackedChange(key={self.key!r}, type={self.change_type.value}, "
            f"old={self.old_value!r}, new={self.new_value!r})"
        )


@dataclass
class TrackResult:
    env_name: str
    changes: List[TrackedChange] = field(default_factory=list)

    @property
    def added_count(self) -> int:
        return sum(1 for c in self.changes if c.change_type == ChangeType.ADDED)

    @property
    def removed_count(self) -> int:
        return sum(1 for c in self.changes if c.change_type == ChangeType.REMOVED)

    @property
    def modified_count(self) -> int:
        return sum(1 for c in self.changes if c.change_type == ChangeType.MODIFIED)

    @property
    def unchanged_count(self) -> int:
        return sum(1 for c in self.changes if c.change_type == ChangeType.UNCHANGED)

    @property
    def has_changes(self) -> bool:
        return any(
            c.change_type != ChangeType.UNCHANGED for c in self.changes
        )


def track_changes(
    old_env: Dict[str, str],
    new_env: Dict[str, str],
    env_name: str = "env",
) -> TrackResult:
    """Compare two env dicts and return a TrackResult describing all changes."""
    changes: List[TrackedChange] = []
    all_keys = sorted(set(old_env) | set(new_env))

    for key in all_keys:
        in_old = key in old_env
        in_new = key in new_env

        if in_old and not in_new:
            changes.append(TrackedChange(key, ChangeType.REMOVED, old_env[key], None))
        elif in_new and not in_old:
            changes.append(TrackedChange(key, ChangeType.ADDED, None, new_env[key]))
        elif old_env[key] != new_env[key]:
            changes.append(TrackedChange(key, ChangeType.MODIFIED, old_env[key], new_env[key]))
        else:
            changes.append(TrackedChange(key, ChangeType.UNCHANGED, old_env[key], new_env[key]))

    return TrackResult(env_name=env_name, changes=changes)
