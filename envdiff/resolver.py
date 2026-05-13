"""Resolve missing keys in a target env by suggesting values from a source env."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class ResolveSuggestion:
    """A suggested value to fill a missing key in the target env."""

    key: str
    suggested_value: str
    source_name: str
    reason: str

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ResolveSuggestion(key={self.key!r}, "
            f"suggested_value={self.suggested_value!r}, "
            f"source={self.source_name!r})"
        )


@dataclass
class ResolveResult:
    """Outcome of resolving missing keys for a target env."""

    source_name: str
    target_name: str
    suggestions: List[ResolveSuggestion] = field(default_factory=list)

    @property
    def suggestion_count(self) -> int:
        return len(self.suggestions)

    @property
    def has_suggestions(self) -> bool:
        return bool(self.suggestions)

    def as_dict(self) -> Dict[str, str]:
        """Return a plain dict mapping key -> suggested_value."""
        return {s.key: s.suggested_value for s in self.suggestions}


def resolve_missing(
    diff: DiffResult,
    placeholder: Optional[str] = None,
) -> ResolveResult:
    """Build suggestions for every key missing in the target.

    If *placeholder* is provided it is used as the suggested value instead of
    the actual source value (useful for generating safe template outputs).
    """
    suggestions: List[ResolveSuggestion] = []

    for entry in diff.entries:
        if entry.status is DiffStatus.MISSING_IN_TARGET:
            value = placeholder if placeholder is not None else (entry.source_value or "")
            reason = (
                "placeholder substituted"
                if placeholder is not None
                else "copied from source"
            )
            suggestions.append(
                ResolveSuggestion(
                    key=entry.key,
                    suggested_value=value,
                    source_name=diff.source_name,
                    reason=reason,
                )
            )

    return ResolveResult(
        source_name=diff.source_name,
        target_name=diff.target_name,
        suggestions=suggestions,
    )
