"""Sorting and grouping utilities for diff results."""

from typing import List, Dict
from envdiff.differ import DiffEntry, DiffResult, DiffStatus


def sort_entries_by_status(entries: List[DiffEntry]) -> List[DiffEntry]:
    """Sort diff entries by status priority: MISSING_IN_TARGET, MISSING_IN_SOURCE, MISMATCH, OK."""
    priority = {
        DiffStatus.MISSING_IN_TARGET: 0,
        DiffStatus.MISSING_IN_SOURCE: 1,
        DiffStatus.MISMATCH: 2,
        DiffStatus.OK: 3,
    }
    return sorted(entries, key=lambda e: (priority.get(e.status, 99), e.key))


def sort_entries_by_key(entries: List[DiffEntry]) -> List[DiffEntry]:
    """Sort diff entries alphabetically by key."""
    return sorted(entries, key=lambda e: e.key)


def group_entries_by_status(entries: List[DiffEntry]) -> Dict[DiffStatus, List[DiffEntry]]:
    """Group diff entries by their status."""
    groups: Dict[DiffStatus, List[DiffEntry]] = {
        DiffStatus.MISSING_IN_TARGET: [],
        DiffStatus.MISSING_IN_SOURCE: [],
        DiffStatus.MISMATCH: [],
        DiffStatus.OK: [],
    }
    for entry in entries:
        groups[entry.status].append(entry)
    for status in groups:
        groups[status] = sort_entries_by_key(groups[status])
    return groups


def sorted_diff_result(result: DiffResult, by: str = "status") -> DiffResult:
    """Return a new DiffResult with entries sorted by the given strategy.

    Args:
        result: The original DiffResult.
        by: Sorting strategy — 'status' (default) or 'key'.

    Returns:
        A new DiffResult with sorted entries.
    """
    if by == "key":
        sorted_entries = sort_entries_by_key(result.entries)
    else:
        sorted_entries = sort_entries_by_status(result.entries)

    return DiffResult(
        source_name=result.source_name,
        target_name=result.target_name,
        entries=sorted_entries,
    )
