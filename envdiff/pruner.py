"""Pruner: identify and remove obsolete or redundant keys from an env."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PruneRecord:
    key: str
    value: str
    reason: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"PruneRecord(key={self.key!r}, reason={self.reason!r})"


@dataclass
class PruneResult:
    env_name: str
    records: List[PruneRecord] = field(default_factory=list)
    output_env: Dict[str, str] = field(default_factory=dict)

    @property
    def pruned_count(self) -> int:
        return len(self.records)

    @property
    def is_clean(self) -> bool:
        return len(self.records) == 0


def prune_env(
    env: Dict[str, str],
    reference_keys: Optional[List[str]] = None,
    remove_empty: bool = True,
    remove_duplicates: bool = True,
    env_name: str = "env",
) -> PruneResult:
    """Prune *env* by removing empty values and keys absent from *reference_keys*.

    Args:
        env: The environment dict to prune.
        reference_keys: If provided, keys not in this list are flagged as obsolete.
        remove_empty: When True, keys whose value is an empty string are pruned.
        remove_duplicates: Reserved for future use (values are always unique per key).
        env_name: Label attached to the result.

    Returns:
        A :class:`PruneResult` containing flagged records and the cleaned env.
    """
    records: List[PruneRecord] = []
    output: Dict[str, str] = {}

    seen_values: Dict[str, str] = {}

    for key, value in env.items():
        if remove_empty and value == "":
            records.append(PruneRecord(key=key, value=value, reason="empty_value"))
            continue

        if reference_keys is not None and key not in reference_keys:
            records.append(PruneRecord(key=key, value=value, reason="obsolete_key"))
            continue

        if remove_duplicates and value in seen_values:
            records.append(
                PruneRecord(
                    key=key,
                    value=value,
                    reason=f"duplicate_value_of_{seen_values[value]}",
                )
            )
            continue

        seen_values[value] = key
        output[key] = value

    return PruneResult(env_name=env_name, records=records, output_env=output)
