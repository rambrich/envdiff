"""Patch a .env file by applying diff entries (add missing keys, update mismatched values)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envdiff.differ import DiffEntry, DiffResult, DiffStatus


class PatchAction(str, Enum):
    ADDED = "added"
    UPDATED = "updated"
    SKIPPED = "skipped"


@dataclass
class PatchRecord:
    key: str
    action: PatchAction
    old_value: Optional[str]
    new_value: Optional[str]

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PatchRecord(key={self.key!r}, action={self.action}, "
            f"old={self.old_value!r}, new={self.new_value!r})"
        )


@dataclass
class PatchResult:
    patched_env: Dict[str, str]
    records: List[PatchRecord] = field(default_factory=list)

    @property
    def applied_count(self) -> int:
        return sum(1 for r in self.records if r.action != PatchAction.SKIPPED)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.records if r.action == PatchAction.SKIPPED)


def patch_env(
    base: Dict[str, str],
    diff_result: DiffResult,
    apply_missing: bool = True,
    apply_mismatch: bool = False,
) -> PatchResult:
    """Return a new env dict with diff entries applied.

    Args:
        base: The environment to patch (typically the target env).
        diff_result: The DiffResult produced by comparing source vs target.
        apply_missing: If True, add keys missing in target from source.
        apply_mismatch: If True, overwrite mismatched values with source values.

    Returns:
        A PatchResult containing the updated env and a log of changes.
    """
    patched = dict(base)
    records: List[PatchRecord] = []

    for entry in diff_result.entries:
        if entry.status == DiffStatus.MISSING_IN_TARGET and apply_missing:
            patched[entry.key] = entry.source_value  # type: ignore[assignment]
            records.append(
                PatchRecord(
                    key=entry.key,
                    action=PatchAction.ADDED,
                    old_value=None,
                    new_value=entry.source_value,
                )
            )
        elif entry.status == DiffStatus.VALUE_MISMATCH and apply_mismatch:
            records.append(
                PatchRecord(
                    key=entry.key,
                    action=PatchAction.UPDATED,
                    old_value=entry.target_value,
                    new_value=entry.source_value,
                )
            )
            patched[entry.key] = entry.source_value  # type: ignore[assignment]
        else:
            if entry.status in (DiffStatus.MISSING_IN_TARGET, DiffStatus.VALUE_MISMATCH):
                records.append(
                    PatchRecord(
                        key=entry.key,
                        action=PatchAction.SKIPPED,
                        old_value=entry.target_value,
                        new_value=entry.source_value,
                    )
                )

    return PatchResult(patched_env=patched, records=records)
