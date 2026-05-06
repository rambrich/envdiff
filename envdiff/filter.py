"""Filter diff results by status or key pattern."""

from __future__ import annotations

import fnmatch
from typing import List, Optional

from envdiff.differ import DiffEntry, DiffResult, DiffStatus


def filter_by_status(
    entries: List[DiffEntry],
    statuses: List[DiffStatus],
) -> List[DiffEntry]:
    """Return only entries whose status is in *statuses*."""
    status_set = set(statuses)
    return [e for e in entries if e.status in status_set]


def filter_by_key_pattern(
    entries: List[DiffEntry],
    pattern: str,
) -> List[DiffEntry]:
    """Return only entries whose key matches *pattern* (glob-style)."""
    return [e for e in entries if fnmatch.fnmatch(e.key, pattern)]


def filter_diff_result(
    result: DiffResult,
    *,
    statuses: Optional[List[DiffStatus]] = None,
    key_pattern: Optional[str] = None,
) -> DiffResult:
    """Return a new :class:`DiffResult` with entries filtered by the given
    criteria.  Both filters are applied when provided (AND semantics).

    Parameters
    ----------
    result:
        The original diff result to filter.
    statuses:
        If given, only entries with one of these statuses are kept.
    key_pattern:
        If given, only entries whose key matches this glob pattern are kept.
    """
    entries = list(result.entries)

    if statuses is not None:
        entries = filter_by_status(entries, statuses)

    if key_pattern is not None:
        entries = filter_by_key_pattern(entries, key_pattern)

    return DiffResult(
        source_name=result.source_name,
        target_name=result.target_name,
        entries=entries,
    )
