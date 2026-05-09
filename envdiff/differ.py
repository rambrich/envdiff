"""Core diffing logic for comparing .env files across environments."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class DiffStatus(str, Enum):
    MISSING_IN_TARGET = "missing_in_target"
    MISSING_IN_SOURCE = "missing_in_source"
    VALUE_MISMATCH = "value_mismatch"
    OK = "ok"


@dataclass
class DiffEntry:
    key: str
    status: DiffStatus
    source_value: Optional[str] = None
    target_value: Optional[str] = None

    def __repr__(self) -> str:
        return (
            f"DiffEntry(key={self.key!r}, status={self.status.value}, "
            f"source={self.source_value!r}, target={self.target_value!r})"
        )


@dataclass
class DiffResult:
    source_name: str
    target_name: str
    entries: List[DiffEntry] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return any(e.status != DiffStatus.OK for e in self.entries)

    @property
    def missing_in_target(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.MISSING_IN_TARGET]

    @property
    def missing_in_source(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.MISSING_IN_SOURCE]

    @property
    def mismatched(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.VALUE_MISMATCH]

    def summary(self) -> str:
        """Return a human-readable summary of the diff result."""
        lines = [
            f"Diff: {self.source_name} -> {self.target_name}",
            f"  Missing in {self.target_name}: {len(self.missing_in_target)}",
            f"  Missing in {self.source_name}: {len(self.missing_in_source)}",
            f"  Value mismatches: {len(self.mismatched)}",
        ]
        return "\n".join(lines)


def diff_envs(
    source: Dict[str, str],
    target: Dict[str, str],
    source_name: str = "source",
    target_name: str = "target",
    keys_only: bool = False,
) -> DiffResult:
    """Compare two env dicts and return a DiffResult.

    Args:
        source: Parsed env dict treated as the reference.
        target: Parsed env dict to compare against.
        source_name: Label for the source environment.
        target_name: Label for the target environment.
        keys_only: If True, skip value comparison (only check key presence).
    """
    result = DiffResult(source_name=source_name, target_name=target_name)
    all_keys = set(source) | set(target)

    for key in sorted(all_keys):
        if key in source and key not in target:
            result.entries.append(
                DiffEntry(key=key, status=DiffStatus.MISSING_IN_TARGET, source_value=source[key])
            )
        elif key not in source and key in target:
            result.entries.append(
                DiffEntry(key=key, status=DiffStatus.MISSING_IN_SOURCE, target_value=target[key])
            )
        else:
            if not keys_only and source[key] != target[key]:
                result.entries.append(
                    DiffEntry(
                        key=key,
                        status=DiffStatus.VALUE_MISMATCH,
                        source_value=source[key],
                        target_value=target[key],
                    )
                )
            else:
                result.entries.append(
                    DiffEntry(
                        key=key,
                        status=DiffStatus.OK,
                        source_value=source[key],
                        target_value=target[key],
                    )
                )

    return result
