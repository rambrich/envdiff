"""Pin specific env keys to expected values and detect drift."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PinViolation:
    key: str
    pinned_value: str
    actual_value: Optional[str]
    env_name: str

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PinViolation(key={self.key!r}, "
            f"pinned={self.pinned_value!r}, "
            f"actual={self.actual_value!r})"
        )


@dataclass
class PinResult:
    env_name: str
    violations: List[PinViolation] = field(default_factory=list)

    @property
    def is_pinned(self) -> bool:
        """Return True when all pinned keys match expected values."""
        return len(self.violations) == 0

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def keys_with_violations(self) -> List[str]:
        return [v.key for v in self.violations]


def check_pins(
    env: Dict[str, str],
    pins: Dict[str, str],
    env_name: str = "env",
) -> PinResult:
    """Compare *env* against the pinned key→value mapping.

    A violation is raised for each pinned key whose value in *env* differs
    from the expected pinned value, or is absent entirely.
    """
    violations: List[PinViolation] = []
    for key, expected in pins.items():
        actual = env.get(key)
        if actual != expected:
            violations.append(
                PinViolation(
                    key=key,
                    pinned_value=expected,
                    actual_value=actual,
                    env_name=env_name,
                )
            )
    return PinResult(env_name=env_name, violations=violations)
