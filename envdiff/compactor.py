"""Compactor: merge duplicate or redundant keys within a single env dict.

Reduces an env mapping by applying a priority-ordered list of env dicts,
producing a single compacted env with provenance records.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CompactRecord:
    key: str
    chosen_value: str
    source_name: str
    alternatives: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"CompactRecord(key={self.key!r}, chosen={self.chosen_value!r}, "
            f"from={self.source_name!r}, alternatives={self.alternatives})"
        )


@dataclass
class CompactResult:
    env_name: str
    records: List[CompactRecord] = field(default_factory=list)

    @property
    def output_env(self) -> Dict[str, str]:
        return {r.key: r.chosen_value for r in self.records}

    @property
    def conflict_count(self) -> int:
        return sum(1 for r in self.records if r.alternatives)

    @property
    def is_clean(self) -> bool:
        return self.conflict_count == 0


def compact_envs(
    envs: List[Dict[str, str]],
    names: Optional[List[str]] = None,
    env_name: str = "compacted",
    prefer_last: bool = False,
) -> CompactResult:
    """Compact multiple env dicts into one.

    Args:
        envs: Ordered list of env dicts. Earlier entries have higher priority
              unless *prefer_last* is True.
        names: Optional display names for each env dict.
        env_name: Name to assign to the resulting CompactResult.
        prefer_last: When True, later dicts take priority (last-wins).

    Returns:
        CompactResult with one record per unique key.
    """
    if names is None:
        names = [f"env{i}" for i in range(len(envs))]

    if len(names) != len(envs):
        raise ValueError("Length of 'names' must match length of 'envs'.")

    ordered_pairs = list(zip(names, envs))
    if prefer_last:
        ordered_pairs = list(reversed(ordered_pairs))

    # Collect all keys across all envs
    all_keys: List[str] = []
    seen: set = set()
    for _, env in ordered_pairs:
        for k in env:
            if k not in seen:
                all_keys.append(k)
                seen.add(k)

    records: List[CompactRecord] = []
    for key in sorted(all_keys):
        chosen_value: Optional[str] = None
        chosen_name: str = ""
        alternatives: List[str] = []

        for name, env in ordered_pairs:
            if key in env:
                if chosen_value is None:
                    chosen_value = env[key]
                    chosen_name = name
                elif env[key] != chosen_value:
                    alternatives.append(env[key])

        records.append(
            CompactRecord(
                key=key,
                chosen_value=chosen_value or "",
                source_name=chosen_name,
                alternatives=alternatives,
            )
        )

    return CompactResult(env_name=env_name, records=records)
