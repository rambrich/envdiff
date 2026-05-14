"""Audit trail for env diff operations — records what changed, when, and why."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class AuditEntry:
    timestamp: str
    operation: str
    source: str
    target: Optional[str]
    key: str
    detail: str

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"AuditEntry(op={self.operation!r}, key={self.key!r}, "
            f"source={self.source!r}, target={self.target!r})"
        )


@dataclass
class AuditLog:
    env_name: str
    entries: List[AuditEntry] = field(default_factory=list)

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    def for_key(self, key: str) -> List[AuditEntry]:
        return [e for e in self.entries if e.key == key]

    def for_operation(self, operation: str) -> List[AuditEntry]:
        return [e for e in self.entries if e.operation == operation]


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def audit_diff_result(diff_result, *, env_name: str = "audit") -> AuditLog:
    """Build an AuditLog from a DiffResult, recording each entry's operation."""
    from envdiff.differ import DiffStatus

    op_map = {
        DiffStatus.MATCH: "match",
        DiffStatus.MISSING_IN_TARGET: "missing_in_target",
        DiffStatus.MISSING_IN_SOURCE: "missing_in_source",
        DiffStatus.VALUE_MISMATCH: "value_mismatch",
    }

    log = AuditLog(env_name=env_name)
    ts = _now_iso()
    for entry in diff_result.entries:
        operation = op_map.get(entry.status, "unknown")
        detail = f"status={entry.status.value}"
        if entry.status == DiffStatus.VALUE_MISMATCH:
            detail += f"; source_value={entry.source_value!r}; target_value={entry.target_value!r}"
        log.entries.append(
            AuditEntry(
                timestamp=ts,
                operation=operation,
                source=diff_result.source_name,
                target=diff_result.target_name,
                key=entry.key,
                detail=detail,
            )
        )
    return log
