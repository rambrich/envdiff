"""Annotator module: attach human-readable annotations/descriptions to diff entries."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffEntry, DiffResult, DiffStatus


@dataclass
class AnnotatedEntry:
    """A diff entry paired with an optional annotation string."""

    entry: DiffEntry
    annotation: Optional[str] = None

    def __repr__(self) -> str:  # pragma: no cover
        return f"AnnotatedEntry(key={self.entry.key!r}, annotation={self.annotation!r})"


@dataclass
class AnnotatedResult:
    """A diff result whose entries have been annotated."""

    source: str
    target: str
    entries: list = field(default_factory=list)  # list[AnnotatedEntry]

    @property
    def has_issues(self) -> bool:
        return any(e.entry.status != DiffStatus.MATCH for e in self.entries)

    def issues(self) -> List["AnnotatedEntry"]:
        """Return only the entries that are not a clean match."""
        return [e for e in self.entries if e.entry.status != DiffStatus.MATCH]


_DEFAULT_ANNOTATIONS: Dict[DiffStatus, str] = {
    DiffStatus.MATCH: "Key exists in both environments with the same value.",
    DiffStatus.MISSING_IN_TARGET: "Key is defined in source but absent from target.",
    DiffStatus.MISSING_IN_SOURCE: "Key is defined in target but absent from source.",
    DiffStatus.MISMATCH: "Key exists in both environments but values differ.",
}


def annotate_entry(
    entry: DiffEntry,
    custom_annotations: Optional[Dict[str, str]] = None,
) -> AnnotatedEntry:
    """Return an AnnotatedEntry for *entry*.

    If *custom_annotations* contains a mapping for ``entry.key`` that text is
    used; otherwise the default status-based annotation is applied.
    """
    if custom_annotations and entry.key in custom_annotations:
        annotation = custom_annotations[entry.key]
    else:
        annotation = _DEFAULT_ANNOTATIONS.get(entry.status)
    return AnnotatedEntry(entry=entry, annotation=annotation)


def annotate_diff_result(
    result: DiffResult,
    custom_annotations: Optional[Dict[str, str]] = None,
) -> AnnotatedResult:
    """Annotate every entry in *result* and return an :class:`AnnotatedResult`."""
    annotated_entries = [
        annotate_entry(e, custom_annotations) for e in result.entries
    ]
    return AnnotatedResult(
        source=result.source,
        target=result.target,
        entries=annotated_entries,
    )
