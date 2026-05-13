"""Compute per-key change frequency statistics across multiple diff results."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class KeyFrequency:
    """How often a key appears with a given status across many diffs."""

    key: str
    status_counts: dict = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.status_counts.values())

    @property
    def most_common_status(self) -> str:
        if not self.status_counts:
            return DiffStatus.MATCH.value
        return max(self.status_counts, key=lambda s: self.status_counts[s])

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"KeyFrequency(key={self.key!r}, total={self.total}, "
            f"most_common={self.most_common_status!r})"
        )


@dataclass
class DiffStatsResult:
    """Aggregated statistics across a collection of DiffResults."""

    diff_count: int
    key_frequencies: List[KeyFrequency]

    @property
    def most_volatile_key(self) -> str | None:
        """Key with the highest count of non-MATCH statuses."""
        best = None
        best_score = -1
        for kf in self.key_frequencies:
            non_match = sum(
                v for s, v in kf.status_counts.items() if s != DiffStatus.MATCH.value
            )
            if non_match > best_score:
                best_score = non_match
                best = kf.key
        return best

    @property
    def stable_keys(self) -> List[str]:
        """Keys that are MATCH in every diff they appear in."""
        result = []
        for kf in self.key_frequencies:
            statuses = set(kf.status_counts.keys())
            if statuses == {DiffStatus.MATCH.value}:
                result.append(kf.key)
        return sorted(result)


def compute_diff_stats(results: List[DiffResult]) -> DiffStatsResult:
    """Aggregate key-level statistics from a list of DiffResults."""
    key_status_counter: dict[str, Counter] = {}

    for result in results:
        for entry in result.entries:
            counter = key_status_counter.setdefault(entry.key, Counter())
            counter[entry.status.value] += 1

    frequencies = [
        KeyFrequency(key=k, status_counts=dict(counter))
        for k, counter in sorted(key_status_counter.items())
    ]

    return DiffStatsResult(diff_count=len(results), key_frequencies=frequencies)
