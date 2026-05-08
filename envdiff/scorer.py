"""Scoring module: assigns a health score to a diff result."""
from dataclasses import dataclass
from typing import Optional

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class DiffScore:
    """Numeric health score for a diff result."""
    source: str
    target: str
    total_keys: int
    match_count: int
    missing_in_target_count: int
    missing_in_source_count: int
    mismatch_count: int
    score: float  # 0.0 – 100.0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DiffScore(source={self.source!r}, target={self.target!r}, "
            f"score={self.score:.1f})"
        )

    @property
    def grade(self) -> str:
        """Letter grade derived from the numeric score."""
        if self.score >= 90:
            return "A"
        if self.score >= 75:
            return "B"
        if self.score >= 50:
            return "C"
        if self.score >= 25:
            return "D"
        return "F"


def score_diff(result: DiffResult, mismatch_weight: float = 0.5) -> DiffScore:
    """Compute a 0-100 health score for *result*.

    Missing keys are penalised fully (1 point each); mismatches are
    penalised by *mismatch_weight* (default 0.5) so they hurt less than
    a fully absent key.
    """
    entries = result.entries
    total = len(entries)
    if total == 0:
        return DiffScore(
            source=result.source,
            target=result.target,
            total_keys=0,
            match_count=0,
            missing_in_target_count=0,
            missing_in_source_count=0,
            mismatch_count=0,
            score=100.0,
        )

    matches = sum(1 for e in entries if e.status == DiffStatus.MATCH)
    missing_target = sum(1 for e in entries if e.status == DiffStatus.MISSING_IN_TARGET)
    missing_source = sum(1 for e in entries if e.status == DiffStatus.MISSING_IN_SOURCE)
    mismatches = sum(1 for e in entries if e.status == DiffStatus.MISMATCH)

    penalty = missing_target + missing_source + mismatches * mismatch_weight
    raw_score = max(0.0, (total - penalty) / total * 100)

    return DiffScore(
        source=result.source,
        target=result.target,
        total_keys=total,
        match_count=matches,
        missing_in_target_count=missing_target,
        missing_in_source_count=missing_source,
        mismatch_count=mismatches,
        score=round(raw_score, 2),
    )
