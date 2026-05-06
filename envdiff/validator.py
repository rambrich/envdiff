"""Validator module for envdiff — checks env values against expected patterns or rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ValidationRule:
    """A single validation rule for a key."""

    key: str
    pattern: Optional[str] = None  # regex pattern the value must match
    required: bool = True  # whether the key must be present
    description: str = ""


@dataclass
class ValidationViolation:
    """Represents a single validation failure."""

    key: str
    message: str
    value: Optional[str] = None

    def __repr__(self) -> str:  # pragma: no cover
        return f"ValidationViolation(key={self.key!r}, message={self.message!r})"


@dataclass
class ValidationResult:
    """Aggregated result of validating an env mapping against a set of rules."""

    env_name: str
    violations: List[ValidationViolation] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.violations) == 0

    def add_violation(self, key: str, message: str, value: Optional[str] = None) -> None:
        self.violations.append(ValidationViolation(key=key, message=message, value=value))


def validate_env(
    env: Dict[str, str],
    rules: List[ValidationRule],
    env_name: str = "env",
) -> ValidationResult:
    """Validate an env mapping against a list of rules.

    Args:
        env: Parsed env mapping (key -> value).
        rules: List of ValidationRule objects to enforce.
        env_name: Human-readable name for the environment being validated.

    Returns:
        A ValidationResult containing any violations found.
    """
    result = ValidationResult(env_name=env_name)

    for rule in rules:
        value = env.get(rule.key)

        if value is None:
            if rule.required:
                result.add_violation(
                    key=rule.key,
                    message=f"Required key '{rule.key}' is missing.",
                )
            continue

        if rule.pattern is not None:
            if not re.fullmatch(rule.pattern, value):
                result.add_violation(
                    key=rule.key,
                    message=(
                        f"Value for '{rule.key}' does not match "
                        f"expected pattern '{rule.pattern}'."
                    ),
                    value=value,
                )

    return result
