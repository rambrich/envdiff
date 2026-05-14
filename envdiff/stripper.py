"""Strip unused or stale keys from a target env based on a reference source."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class StripRecord:
    key: str
    value: str
    reason: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"StripRecord(key={self.key!r}, reason={self.reason!r})"


@dataclass
class StripResult:
    env_name: str
    output_env: Dict[str, str]
    stripped: List[StripRecord] = field(default_factory=list)

    @property
    def stripped_count(self) -> int:
        return len(self.stripped)

    @property
    def is_clean(self) -> bool:
        return len(self.stripped) == 0


def strip_keys(
    env: Dict[str, str],
    reference: Dict[str, str],
    env_name: str = "env",
) -> StripResult:
    """Remove keys from *env* that are not present in *reference*.

    Args:
        env: The environment dict to strip.
        reference: The authoritative set of keys.
        env_name: Label used in the result.

    Returns:
        A :class:`StripResult` with the cleaned env and a record of
        every key that was removed.
    """
    stripped: List[StripRecord] = []
    output: Dict[str, str] = {}

    for key, value in env.items():
        if key in reference:
            output[key] = value
        else:
            stripped.append(
                StripRecord(
                    key=key,
                    value=value,
                    reason="not present in reference",
                )
            )

    return StripResult(env_name=env_name, output_env=output, stripped=stripped)
