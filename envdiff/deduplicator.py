"""Deduplicator: merge duplicate keys in an env dict by applying a chosen strategy."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple


class DedupeStrategy(str, Enum):
    FIRST = "first"   # keep the first occurrence
    LAST = "last"    # keep the last occurrence
    ERROR = "error"  # raise on any duplicate


@dataclass
class DedupeRecord:
    key: str
    kept_value: str
    discarded_values: List[str]

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DedupeRecord(key={self.key!r}, kept={self.kept_value!r}, "
            f"discarded={self.discarded_values!r})"
        )


@dataclass
class DedupeResult:
    env_name: str
    output_env: Dict[str, str]
    records: List[DedupeRecord] = field(default_factory=list)

    @property
    def deduped_count(self) -> int:
        return len(self.records)

    @property
    def is_clean(self) -> bool:
        return self.deduped_count == 0


def deduplicate(
    pairs: List[Tuple[str, str]],
    strategy: DedupeStrategy = DedupeStrategy.FIRST,
    env_name: str = "",
) -> DedupeResult:
    """Deduplicate a list of (key, value) pairs (preserving insertion order).

    ``pairs`` may contain the same key multiple times, which is valid in raw
    .env files parsed line-by-line before uniqueness is enforced.
    """
    if strategy is DedupeStrategy.ERROR:
        seen: Dict[str, int] = {}
        for key, _ in pairs:
            seen[key] = seen.get(key, 0) + 1
        dupes = [k for k, c in seen.items() if c > 1]
        if dupes:
            raise ValueError(
                f"Duplicate keys found with strategy=error: {dupes}"
            )

    buckets: Dict[str, List[str]] = {}
    order: List[str] = []
    for key, value in pairs:
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(value)

    output_env: Dict[str, str] = {}
    records: List[DedupeRecord] = []

    for key in order:
        values = buckets[key]
        if len(values) == 1:
            output_env[key] = values[0]
        else:
            kept = values[0] if strategy is DedupeStrategy.FIRST else values[-1]
            discarded = values[1:] if strategy is DedupeStrategy.FIRST else values[:-1]
            output_env[key] = kept
            records.append(DedupeRecord(key=key, kept_value=kept, discarded_values=discarded))

    return DedupeResult(env_name=env_name, output_env=output_env, records=records)
