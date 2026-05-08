"""Rename keys across env dicts using a mapping of old -> new names."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RenameRecord:
    old_key: str
    new_key: str
    applied: bool  # False if old_key was not present in the env

    def __repr__(self) -> str:  # pragma: no cover
        status = "applied" if self.applied else "skipped"
        return f"RenameRecord({self.old_key!r} -> {self.new_key!r}, {status})"


@dataclass
class RenameResult:
    original: Dict[str, str]
    renamed: Dict[str, str]
    records: List[RenameRecord] = field(default_factory=list)

    @property
    def applied_count(self) -> int:
        return sum(1 for r in self.records if r.applied)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.records if not r.applied)


def rename_keys(
    env: Dict[str, str],
    mapping: Dict[str, str],
    *,
    remove_old: bool = True,
) -> RenameResult:
    """Return a copy of *env* with keys renamed according to *mapping*.

    Args:
        env: Source environment dict.
        mapping: ``{old_key: new_key}`` pairs.
        remove_old: When ``True`` (default) the old key is removed from the
            result.  Set to ``False`` to keep both keys.

    Returns:
        :class:`RenameResult` describing what changed.
    """
    result: Dict[str, str] = dict(env)
    records: List[RenameRecord] = []

    for old_key, new_key in mapping.items():
        if old_key in result:
            result[new_key] = result[old_key]
            if remove_old:
                del result[old_key]
            records.append(RenameRecord(old_key=old_key, new_key=new_key, applied=True))
        else:
            records.append(RenameRecord(old_key=old_key, new_key=new_key, applied=False))

    return RenameResult(original=dict(env), renamed=result, records=records)
