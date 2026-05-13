"""Normalize .env values for consistent comparison (trim whitespace, unquote strings)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class NormalizeRecord:
    key: str
    original: str
    normalized: str

    @property
    def changed(self) -> bool:
        return self.original != self.normalized

    def __repr__(self) -> str:  # pragma: no cover
        return f"NormalizeRecord(key={self.key!r}, changed={self.changed})"


@dataclass
class NormalizeResult:
    env_name: str
    records: List[NormalizeRecord] = field(default_factory=list)

    @property
    def output_env(self) -> Dict[str, str]:
        return {r.key: r.normalized for r in self.records}

    @property
    def changed_count(self) -> int:
        return sum(1 for r in self.records if r.changed)

    @property
    def unchanged_count(self) -> int:
        return len(self.records) - self.changed_count


def _normalize_value(value: str) -> str:
    """Strip surrounding whitespace and remove matching outer quotes."""
    value = value.strip()
    if len(value) >= 2:
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
    return value


def normalize_env(
    env: Dict[str, str],
    env_name: str = "env",
) -> NormalizeResult:
    """Normalize all values in *env* and return a NormalizeResult."""
    records: List[NormalizeRecord] = []
    for key in sorted(env):
        original = env[key]
        normalized = _normalize_value(original)
        records.append(NormalizeRecord(key=key, original=original, normalized=normalized))
    return NormalizeResult(env_name=env_name, records=records)
