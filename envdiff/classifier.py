"""Classify env keys into semantic categories based on naming patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List


CATEGORY_PATTERNS: Dict[str, List[str]] = {
    "database": [r"DB_", r"DATABASE_", r"POSTGRES", r"MYSQL", r"MONGO", r"REDIS"],
    "auth": [r"SECRET", r"TOKEN", r"API_KEY", r"AUTH_", r"JWT", r"PASSWORD", r"PASSWD"],
    "network": [r"HOST", r"PORT", r"URL", r"ENDPOINT", r"DOMAIN", r"BASE_URL"],
    "feature_flag": [r"FEATURE_", r"FLAG_", r"ENABLE_", r"DISABLE_"],
    "logging": [r"LOG_", r"LOGGING_", r"DEBUG", r"VERBOSE"],
    "storage": [r"S3_", r"BUCKET", r"STORAGE_", r"UPLOAD_"],
    "email": [r"SMTP", r"MAIL_", r"EMAIL_", r"SENDGRID"],
}


@dataclass
class ClassifiedKey:
    key: str
    category: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"ClassifiedKey(key={self.key!r}, category={self.category!r})"


@dataclass
class ClassifyResult:
    env_name: str
    entries: List[ClassifiedKey] = field(default_factory=list)

    def keys_for_category(self, category: str) -> List[str]:
        """Return all keys belonging to the given category."""
        return [e.key for e in self.entries if e.category == category]

    def categories(self) -> List[str]:
        """Return sorted list of distinct categories present."""
        return sorted({e.category for e in self.entries})

    def category_for_key(self, key: str) -> str | None:
        """Return the category for a specific key, or None if not found."""
        for entry in self.entries:
            if entry.key == key:
                return entry.category
        return None


def _classify_key(key: str, patterns: Dict[str, List[str]] | None = None) -> str:
    """Return the first matching category for *key*, or 'other'."""
    if patterns is None:
        patterns = CATEGORY_PATTERNS
    upper = key.upper()
    for category, regexes in patterns.items():
        for pattern in regexes:
            if re.search(pattern, upper):
                return category
    return "other"


def classify_env(
    env: Dict[str, str],
    env_name: str = "env",
    patterns: Dict[str, List[str]] | None = None,
) -> ClassifyResult:
    """Classify every key in *env* and return a :class:`ClassifyResult`."""
    entries = [
        ClassifiedKey(key=k, category=_classify_key(k, patterns))
        for k in sorted(env.keys())
    ]
    return ClassifyResult(env_name=env_name, entries=entries)
