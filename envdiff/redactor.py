"""Redactor module: mask sensitive values in env diffs and profiles."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

# Default patterns that indicate a key holds a sensitive value
DEFAULT_SENSITIVE_PATTERNS: list[str] = [
    r"(?i)password",
    r"(?i)secret",
    r"(?i)token",
    r"(?i)api[_-]?key",
    r"(?i)private[_-]?key",
    r"(?i)auth",
    r"(?i)credential",
    r"(?i)passphrase",
]

DEFAULT_MASK = "***REDACTED***"


@dataclass
class RedactorConfig:
    """Configuration for the redactor."""

    patterns: list[str] = field(default_factory=lambda: list(DEFAULT_SENSITIVE_PATTERNS))
    mask: str = DEFAULT_MASK
    _compiled: list[re.Pattern] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._compiled = [re.compile(p) for p in self.patterns]

    def is_sensitive(self, key: str) -> bool:
        """Return True if *key* matches any sensitive pattern."""
        return any(p.search(key) for p in self._compiled)


def redact_value(key: str, value: str | None, config: RedactorConfig) -> str | None:
    """Return *mask* if *key* is sensitive, otherwise return *value* unchanged."""
    if value is None:
        return None
    return config.mask if config.is_sensitive(key) else value


def redact_env(
    env: dict[str, str | None],
    config: RedactorConfig | None = None,
) -> dict[str, str | None]:
    """Return a copy of *env* with sensitive values replaced by the mask."""
    cfg = config or RedactorConfig()
    return {k: redact_value(k, v, cfg) for k, v in env.items()}


def redact_keys(
    keys: Iterable[str],
    config: RedactorConfig | None = None,
) -> list[str]:
    """Return the subset of *keys* that are considered sensitive."""
    cfg = config or RedactorConfig()
    return [k for k in keys if cfg.is_sensitive(k)]
