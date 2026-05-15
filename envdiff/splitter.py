"""Split a merged .env dict into multiple env dicts based on key prefix groups."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SplitGroup:
    """A single prefix group produced by splitting an env."""

    prefix: str
    env: Dict[str, str]

    def __repr__(self) -> str:  # pragma: no cover
        return f"SplitGroup(prefix={self.prefix!r}, keys={list(self.env)})"

    @property
    def key_count(self) -> int:
        return len(self.env)


@dataclass
class SplitResult:
    """Result of splitting an env dict by prefix."""

    env_name: str
    groups: List[SplitGroup] = field(default_factory=list)
    remainder: Dict[str, str] = field(default_factory=dict)

    @property
    def group_names(self) -> List[str]:
        return [g.prefix for g in self.groups]

    @property
    def total_grouped_keys(self) -> int:
        return sum(g.key_count for g in self.groups)

    def get_group(self, prefix: str) -> Optional[SplitGroup]:
        for g in self.groups:
            if g.prefix == prefix:
                return g
        return None


def split_env_by_prefix(
    env: Dict[str, str],
    prefixes: List[str],
    *,
    env_name: str = "env",
    strip_prefix: bool = False,
    separator: str = "_",
) -> SplitResult:
    """Split *env* into groups based on *prefixes*.

    Keys that match no prefix land in ``SplitResult.remainder``.

    Args:
        env: The source environment dictionary.
        prefixes: Ordered list of prefixes to split on (e.g. ``["DB", "AWS"]``).
        env_name: Label stored on the result.
        strip_prefix: When *True* the prefix (+ separator) is removed from the
            key inside each group dict.
        separator: Character that follows the prefix in the key name.
    """
    claimed: set[str] = set()
    groups: List[SplitGroup] = []

    for prefix in prefixes:
        token = prefix.upper() + separator
        group_env: Dict[str, str] = {}
        for key, value in env.items():
            if key.upper().startswith(token):
                stored_key = key[len(token):] if strip_prefix else key
                group_env[stored_key] = value
                claimed.add(key)
        groups.append(SplitGroup(prefix=prefix, env=group_env))

    remainder = {k: v for k, v in env.items() if k not in claimed}
    return SplitResult(env_name=env_name, groups=groups, remainder=remainder)
