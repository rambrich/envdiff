"""Tests for envdiff.annotator."""

import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.annotator import (
    AnnotatedEntry,
    AnnotatedResult,
    annotate_entry,
    annotate_diff_result,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_entries():
    return [
        DiffEntry(key="MATCH_KEY", status=DiffStatus.MATCH, source_value="v", target_value="v"),
        DiffEntry(key="MISSING_T", status=DiffStatus.MISSING_IN_TARGET, source_value="v", target_value=None),
        DiffEntry(key="MISSING_S", status=DiffStatus.MISSING_IN_SOURCE, source_value=None, target_value="v"),
        DiffEntry(key="MISMATCH", status=DiffStatus.MISMATCH, source_value="a", target_value="b"),
    ]


@pytest.fixture()
def diff_result(sample_entries):
    return DiffResult(source="dev", target="prod", entries=sample_entries)


# ---------------------------------------------------------------------------
# annotate_entry
# ---------------------------------------------------------------------------


def test_annotate_entry_returns_annotated_entry(sample_entries):
    ae = annotate_entry(sample_entries[0])
    assert isinstance(ae, AnnotatedEntry)
    assert ae.entry is sample_entries[0]


def test_annotate_entry_match_default_annotation(sample_entries):
    ae = annotate_entry(sample_entries[0])
    assert ae.annotation is not None
    assert "both" in ae.annotation.lower()


def test_annotate_entry_missing_in_target_annotation(sample_entries):
    ae = annotate_entry(sample_entries[1])
    assert "target" in ae.annotation.lower()


def test_annotate_entry_missing_in_source_annotation(sample_entries):
    ae = annotate_entry(sample_entries[2])
    assert "source" in ae.annotation.lower()


def test_annotate_entry_mismatch_annotation(sample_entries):
    ae = annotate_entry(sample_entries[3])
    assert "differ" in ae.annotation.lower()


def test_annotate_entry_custom_annotation_overrides_default(sample_entries):
    custom = {"MISMATCH": "Intentional override for this key."}
    ae = annotate_entry(sample_entries[3], custom_annotations=custom)
    assert ae.annotation == "Intentional override for this key."


def test_annotate_entry_custom_annotation_ignores_other_keys(sample_entries):
    custom = {"OTHER_KEY": "should not appear"}
    ae = annotate_entry(sample_entries[0], custom_annotations=custom)
    assert ae.annotation != "should not appear"


# ---------------------------------------------------------------------------
# annotate_diff_result
# ---------------------------------------------------------------------------


def test_annotate_diff_result_returns_annotated_result(diff_result):
    ar = annotate_diff_result(diff_result)
    assert isinstance(ar, AnnotatedResult)


def test_annotate_diff_result_preserves_source_target(diff_result):
    ar = annotate_diff_result(diff_result)
    assert ar.source == "dev"
    assert ar.target == "prod"


def test_annotate_diff_result_entry_count(diff_result):
    ar = annotate_diff_result(diff_result)
    assert len(ar.entries) == len(diff_result.entries)


def test_annotate_diff_result_all_annotated(diff_result):
    ar = annotate_diff_result(diff_result)
    assert all(isinstance(e, AnnotatedEntry) for e in ar.entries)
    assert all(e.annotation is not None for e in ar.entries)


def test_annotate_diff_result_has_issues_true(diff_result):
    ar = annotate_diff_result(diff_result)
    assert ar.has_issues is True


def test_annotate_diff_result_has_issues_false():
    entries = [DiffEntry(key="K", status=DiffStatus.MATCH, source_value="v", target_value="v")]
    result = DiffResult(source="a", target="b", entries=entries)
    ar = annotate_diff_result(result)
    assert ar.has_issues is False


def test_annotate_diff_result_custom_annotations_applied(diff_result):
    custom = {"MISSING_T": "Custom note for missing target key."}
    ar = annotate_diff_result(diff_result, custom_annotations=custom)
    annotated = next(e for e in ar.entries if e.entry.key == "MISSING_T")
    assert annotated.annotation == "Custom note for missing target key."
