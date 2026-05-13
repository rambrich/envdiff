"""Plan the steps needed to reconcile two .env environments."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from envdiff.differ import DiffResult, DiffStatus


class PlanAction(str, Enum):
    ADD = "add"          # key is missing in target — add it
    REMOVE = "remove"    # key is missing in source — remove from target
    UPDATE = "update"    # key exists in both but values differ
    KEEP = "keep"        # key matches — no action needed


@dataclass
class PlanStep:
    key: str
    action: PlanAction
    source_value: str | None
    target_value: str | None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PlanStep(key={self.key!r}, action={self.action.value}, "
            f"source={self.source_value!r}, target={self.target_value!r})"
        )


@dataclass
class PlanResult:
    source_name: str
    target_name: str
    steps: List[PlanStep] = field(default_factory=list)

    @property
    def action_count(self) -> int:
        return sum(1 for s in self.steps if s.action != PlanAction.KEEP)

    @property
    def is_noop(self) -> bool:
        return self.action_count == 0

    def steps_for_action(self, action: PlanAction) -> List[PlanStep]:
        return [s for s in self.steps if s.action == action]


_STATUS_TO_ACTION: dict[DiffStatus, PlanAction] = {
    DiffStatus.MATCH: PlanAction.KEEP,
    DiffStatus.MISSING_IN_TARGET: PlanAction.ADD,
    DiffStatus.MISSING_IN_SOURCE: PlanAction.REMOVE,
    DiffStatus.MISMATCH: PlanAction.UPDATE,
}


def plan_reconciliation(diff: DiffResult) -> PlanResult:
    """Build a PlanResult describing how to make *target* match *source*."""
    steps: List[PlanStep] = []
    for entry in sorted(diff.entries, key=lambda e: e.key):
        action = _STATUS_TO_ACTION[entry.status]
        steps.append(
            PlanStep(
                key=entry.key,
                action=action,
                source_value=entry.source_value,
                target_value=entry.target_value,
            )
        )
    return PlanResult(
        source_name=diff.source_name,
        target_name=diff.target_name,
        steps=steps,
    )
