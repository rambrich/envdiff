"""Matrix comparison: diff one source env against multiple targets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.differ import DiffResult, diff


@dataclass
class MatrixCell:
    """A single cell in the diff matrix (source vs one target)."""

    target_name: str
    result: DiffResult

    @property
    def has_issues(self) -> bool:  # noqa: D401
        return self.result.has_issues


@dataclass
class DiffMatrix:
    """Full matrix of diffs between one source and many targets."""

    source_name: str
    cells: List[MatrixCell] = field(default_factory=list)

    @property
    def target_names(self) -> List[str]:
        return [c.target_name for c in self.cells]

    @property
    def has_any_issues(self) -> bool:
        return any(c.has_issues for c in self.cells)

    @property
    def clean_targets(self) -> List[str]:
        return [c.target_name for c in self.cells if not c.has_issues]

    @property
    def failing_targets(self) -> List[str]:
        return [c.target_name for c in self.cells if c.has_issues]

    def get(self, target_name: str) -> DiffResult | None:
        for cell in self.cells:
            if cell.target_name == target_name:
                return cell.result
        return None


def build_matrix(
    source: Dict[str, str],
    targets: Dict[str, Dict[str, str]],
    source_name: str = "source",
) -> DiffMatrix:
    """Diff *source* against every env in *targets*.

    Parameters
    ----------
    source:
        Parsed source environment.
    targets:
        Mapping of target-name -> parsed environment.
    source_name:
        Label used for the source environment.
    """
    cells: List[MatrixCell] = []
    for target_name, target_env in targets.items():
        result = diff(source, target_env, source_name=source_name, target_name=target_name)
        cells.append(MatrixCell(target_name=target_name, result=result))
    return DiffMatrix(source_name=source_name, cells=cells)
