"""Sanitizer: strip or replace unsafe characters from env values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_NEWLINE_RE = re.compile(r"[\r\n]+")


@dataclass
class SanitizeRecord:
    key: str
    original: str
    sanitized: str

    @property
    def changed(self) -> bool:
        return self.original != self.sanitized

    def __repr__(self) -> str:  # pragma: no cover
        return f"SanitizeRecord(key={self.key!r}, changed={self.changed})"


@dataclass
class SanitizeResult:
    env_name: str
    records: List[SanitizeRecord] = field(default_factory=list)

    @property
    def output_env(self) -> Dict[str, str]:
        return {r.key: r.sanitized for r in self.records}

    @property
    def changed_count(self) -> int:
        return sum(1 for r in self.records if r.changed)

    @property
    def is_clean(self) -> bool:
        return self.changed_count == 0


def sanitize_env(
    env: Dict[str, str],
    env_name: str = "env",
    replace_newlines: bool = True,
    newline_replacement: str = " ",
    strip_control: bool = True,
    strip_whitespace: bool = False,
    custom_pattern: Optional[str] = None,
    custom_replacement: str = "",
) -> SanitizeResult:
    """Sanitize all values in *env* and return a SanitizeResult."""
    custom_re = re.compile(custom_pattern) if custom_pattern else None
    records: List[SanitizeRecord] = []

    for key, value in env.items():
        sanitized = value

        if strip_control:
            sanitized = _CONTROL_RE.sub("", sanitized)

        if replace_newlines:
            sanitized = _NEWLINE_RE.sub(newline_replacement, sanitized)

        if strip_whitespace:
            sanitized = sanitized.strip()

        if custom_re is not None:
            sanitized = custom_re.sub(custom_replacement, sanitized)

        records.append(SanitizeRecord(key=key, original=value, sanitized=sanitized))

    return SanitizeResult(env_name=env_name, records=records)
