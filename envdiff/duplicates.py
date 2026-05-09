"""Detect duplicate keys within a single .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class DuplicateEntry:
    key: str
    line_numbers: List[int]
    values: List[str]

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DuplicateEntry(key={self.key!r}, "
            f"lines={self.line_numbers}, values={self.values})"
        )

    @property
    def count(self) -> int:
        return len(self.line_numbers)


@dataclass
class DuplicateResult:
    env_name: str
    duplicates: List[DuplicateEntry] = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return len(self.duplicates) > 0

    @property
    def duplicate_count(self) -> int:
        return len(self.duplicates)


def find_duplicates(path: str | Path, env_name: str | None = None) -> DuplicateResult:
    """Parse *path* line-by-line and report any duplicated keys."""
    path = Path(path)
    name = env_name or path.name

    seen: Dict[str, List[tuple[int, str]]] = {}

    with path.open(encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            seen.setdefault(key, []).append((lineno, value))

    duplicates = [
        DuplicateEntry(
            key=key,
            line_numbers=[ln for ln, _ in occurrences],
            values=[v for _, v in occurrences],
        )
        for key, occurrences in seen.items()
        if len(occurrences) > 1
    ]

    return DuplicateResult(env_name=name, duplicates=duplicates)
