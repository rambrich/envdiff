"""Tag .env keys with user-defined labels for categorisation."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Optional


@dataclass
class TagRule:
    """A pattern-based rule that assigns a tag to matching keys."""

    tag: str
    pattern: str  # supports fnmatch wildcards, e.g. "DB_*"


@dataclass
class TaggedKey:
    """A single key together with all tags that matched it."""

    key: str
    tags: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"TaggedKey(key={self.key!r}, tags={self.tags!r})"


@dataclass
class TagResult:
    """Outcome of tagging an env dict."""

    env_name: str
    entries: List[TaggedKey] = field(default_factory=list)

    # --- convenience helpers ---

    def keys_for_tag(self, tag: str) -> List[str]:
        """Return all keys that carry *tag*."""
        return [e.key for e in self.entries if tag in e.tags]

    def tags_for_key(self, key: str) -> List[str]:
        """Return all tags assigned to *key*, or an empty list."""
        for e in self.entries:
            if e.key == key:
                return list(e.tags)
        return []

    @property
    def all_tags(self) -> List[str]:
        """Sorted, deduplicated list of every tag present in the result."""
        seen: set[str] = set()
        for e in self.entries:
            seen.update(e.tags)
        return sorted(seen)


def tag_env(
    env: Dict[str, str],
    rules: List[TagRule],
    env_name: str = "env",
    untagged_label: Optional[str] = None,
) -> TagResult:
    """Apply *rules* to every key in *env* and return a :class:`TagResult`.

    Parameters
    ----------
    env:
        Parsed environment mapping ``{key: value}``.
    rules:
        Ordered list of :class:`TagRule` objects.  All matching rules are
        applied (not just the first).
    env_name:
        Human-readable name stored in the result.
    untagged_label:
        When provided, keys that match no rule receive this tag instead of
        being left with an empty tag list.
    """
    entries: List[TaggedKey] = []
    for key in sorted(env):
        tags = [r.tag for r in rules if fnmatch(key, r.pattern)]
        if not tags and untagged_label is not None:
            tags = [untagged_label]
        entries.append(TaggedKey(key=key, tags=tags))
    return TagResult(env_name=env_name, entries=entries)
