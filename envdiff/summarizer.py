"""Summarizer module for envdiff — produces statistical summaries of diff results."""

from dataclasses import dataclass
from typing import Dict

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class DiffSummary:
    """Statistical summary of a DiffResult."""

    source: str
    target: str
    total: int
    counts: Dict[str, int]

    @property
    def match_count(self) -> int:
        return self.counts.get(DiffStatus.MATCH.value, 0)

    @property
    def missing_in_target_count(self) -> int:
        return self.counts.get(DiffStatus.MISSING_IN_TARGET.value, 0)

    @property
    def missing_in_source_count(self) -> int:
        return self.counts.get(DiffStatus.MISSING_IN_SOURCE.value, 0)

    @property
    def mismatch_count(self) -> int:
        return self.counts.get(DiffStatus.MISMATCH.value, 0)

    @property
    def has_issues(self) -> bool:
        return self.total > self.match_count

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "total": self.total,
            "match": self.match_count,
            "missing_in_target": self.missing_in_target_count,
            "missing_in_source": self.missing_in_source_count,
            "mismatch": self.mismatch_count,
            "has_issues": self.has_issues,
        }


def summarize(result: DiffResult) -> DiffSummary:
    """Compute a statistical summary from a DiffResult."""
    counts: Dict[str, int] = {status.value: 0 for status in DiffStatus}
    for entry in result.entries:
        counts[entry.status.value] += 1
    return DiffSummary(
        source=result.source,
        target=result.target,
        total=len(result.entries),
        counts=counts,
    )


def format_summary(summary: DiffSummary) -> str:
    """Return a human-readable summary string."""
    lines = [
        f"Summary: {summary.source} vs {summary.target}",
        f"  Total keys   : {summary.total}",
        f"  Matches      : {summary.match_count}",
        f"  Mismatches   : {summary.mismatch_count}",
        f"  Missing in {summary.target}: {summary.missing_in_target_count}",
        f"  Missing in {summary.source}: {summary.missing_in_source_count}",
    ]
    return "\n".join(lines)
