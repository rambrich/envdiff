"""Score a DiffMatrix across multiple target environments."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from envdiff.differ_matrix import DiffMatrix
from envdiff.scorer import DiffScore, score_diff


@dataclass
class MatrixScoreEntry:
    """Score for a single target within a DiffMatrix."""

    target_name: str
    score: DiffScore

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"MatrixScoreEntry(target={self.target_name!r}, "
            f"score={self.score.score}, grade={self.score.grade})"
        )


@dataclass
class MatrixScoreResult:
    """Aggregated scores for all targets in a DiffMatrix."""

    source_name: str
    entries: List[MatrixScoreEntry]

    @property
    def average_score(self) -> float:
        """Mean score across all target environments (0-100)."""
        if not self.entries:
            return 100.0
        return sum(e.score.score for e in self.entries) / len(self.entries)

    @property
    def lowest_entry(self) -> MatrixScoreEntry | None:
        """Return the target with the lowest score, or None if empty."""
        if not self.entries:
            return None
        return min(self.entries, key=lambda e: e.score.score)

    @property
    def highest_entry(self) -> MatrixScoreEntry | None:
        """Return the target with the highest score, or None if empty."""
        if not self.entries:
            return None
        return max(self.entries, key=lambda e: e.score.score)


def score_matrix(matrix: DiffMatrix) -> MatrixScoreResult:
    """Compute a DiffScore for every target cell in *matrix*."""
    scored: List[MatrixScoreEntry] = []
    for cell in matrix.cells:
        diff_score = score_diff(cell.result)
        scored.append(MatrixScoreEntry(target_name=cell.target_name, score=diff_score))
    return MatrixScoreResult(source_name=matrix.source_name, entries=scored)
