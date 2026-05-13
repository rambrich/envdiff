"""Compute aggregate statistics across multiple diff results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class EnvStatistics:
    """Aggregate statistics computed from one or more DiffResults."""

    total_comparisons: int
    total_entries: int
    total_matches: int
    total_missing_in_target: int
    total_missing_in_source: int
    total_mismatches: int
    unique_keys: List[str] = field(default_factory=list)

    @property
    def match_rate(self) -> float:
        """Fraction of entries that are exact matches (0.0–1.0)."""
        if self.total_entries == 0:
            return 1.0
        return self.total_matches / self.total_entries

    @property
    def issue_rate(self) -> float:
        """Fraction of entries that have any issue (0.0–1.0)."""
        return 1.0 - self.match_rate

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"EnvStatistics(comparisons={self.total_comparisons}, "
            f"entries={self.total_entries}, match_rate={self.match_rate:.2%})"
        )


def compute_statistics(results: List[DiffResult]) -> EnvStatistics:
    """Compute aggregate statistics from a list of DiffResult objects."""
    total_entries = 0
    total_matches = 0
    total_missing_in_target = 0
    total_missing_in_source = 0
    total_mismatches = 0
    all_keys: set[str] = set()

    for result in results:
        for entry in result.entries:
            total_entries += 1
            all_keys.add(entry.key)
            if entry.status == DiffStatus.MATCH:
                total_matches += 1
            elif entry.status == DiffStatus.MISSING_IN_TARGET:
                total_missing_in_target += 1
            elif entry.status == DiffStatus.MISSING_IN_SOURCE:
                total_missing_in_source += 1
            elif entry.status == DiffStatus.MISMATCH:
                total_mismatches += 1

    return EnvStatistics(
        total_comparisons=len(results),
        total_entries=total_entries,
        total_matches=total_matches,
        total_missing_in_target=total_missing_in_target,
        total_missing_in_source=total_missing_in_source,
        total_mismatches=total_mismatches,
        unique_keys=sorted(all_keys),
    )
