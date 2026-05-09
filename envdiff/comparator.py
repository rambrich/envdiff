"""Multi-env comparator: diff one source against multiple targets at once."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.differ import DiffResult, diff
from envdiff.summarizer import DiffSummary, summarize


@dataclass
class CompareResult:
    """Holds diff results for one source compared against many targets."""

    source_name: str
    results: Dict[str, DiffResult] = field(default_factory=dict)
    summaries: Dict[str, DiffSummary] = field(default_factory=dict)

    @property
    def target_names(self) -> List[str]:
        return list(self.results.keys())

    def has_any_issues(self) -> bool:
        return any(r.has_issues() for r in self.results.values())

    def worst_target(self) -> str | None:
        """Return the target name with the most total issues."""
        if not self.summaries:
            return None
        return max(
            self.summaries,
            key=lambda name: (
                self.summaries[name].missing_in_target_count
                + self.summaries[name].missing_in_source_count
                + self.summaries[name].mismatch_count
            ),
        )


def compare_many(
    source_env: Dict[str, str],
    targets: Dict[str, Dict[str, str]],
    source_name: str = "source",
) -> CompareResult:
    """Diff *source_env* against every env in *targets*.

    Args:
        source_env: The reference environment key/value mapping.
        targets: Mapping of target-name -> key/value mapping.
        source_name: Label used for the source in each DiffResult.

    Returns:
        A :class:`CompareResult` containing per-target diffs and summaries.
    """
    result = CompareResult(source_name=source_name)
    for target_name, target_env in targets.items():
        dr = diff(source_env, target_env, source_name=source_name, target_name=target_name)
        result.results[target_name] = dr
        result.summaries[target_name] = summarize(dr)
    return result
