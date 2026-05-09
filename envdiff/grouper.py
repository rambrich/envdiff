"""Group and partition .env entries by key prefix or custom criteria."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffEntry, DiffResult


@dataclass
class GroupedEntries:
    """A named group of DiffEntry objects."""

    name: str
    entries: List[DiffEntry] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"GroupedEntries(name={self.name!r}, count={len(self.entries)})"

    @property
    def count(self) -> int:
        return len(self.entries)


@dataclass
class GroupedResult:
    """Collection of named groups derived from a DiffResult."""

    source: str
    target: str
    groups: Dict[str, GroupedEntries] = field(default_factory=dict)

    @property
    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    def get(self, name: str) -> Optional[GroupedEntries]:
        return self.groups.get(name)


def group_by_prefix(
    result: DiffResult,
    separator: str = "_",
    ungrouped_label: str = "OTHER",
) -> GroupedResult:
    """Partition entries into groups based on the key prefix before *separator*.

    Keys without a separator are collected under *ungrouped_label*.
    """
    grouped = GroupedResult(source=result.source, target=result.target)

    for entry in result.entries:
        if separator in entry.key:
            prefix = entry.key.split(separator, 1)[0].upper()
        else:
            prefix = ungrouped_label.upper()

        if prefix not in grouped.groups:
            grouped.groups[prefix] = GroupedEntries(name=prefix)
        grouped.groups[prefix].entries.append(entry)

    return grouped


def group_by_keys(
    result: DiffResult,
    key_groups: Dict[str, List[str]],
    ungrouped_label: str = "OTHER",
) -> GroupedResult:
    """Partition entries into explicitly defined groups by key membership.

    Keys not listed in any group land in *ungrouped_label*.
    """
    reverse_map: Dict[str, str] = {}
    for group_name, keys in key_groups.items():
        for k in keys:
            reverse_map[k] = group_name.upper()

    grouped = GroupedResult(source=result.source, target=result.target)

    for entry in result.entries:
        label = reverse_map.get(entry.key, ungrouped_label.upper())
        if label not in grouped.groups:
            grouped.groups[label] = GroupedEntries(name=label)
        grouped.groups[label].entries.append(entry)

    return grouped
