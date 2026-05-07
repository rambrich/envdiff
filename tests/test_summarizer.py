"""Tests for envdiff.summarizer module."""

import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.summarizer import DiffSummary, format_summary, summarize


@pytest.fixture
def result():
    entries = [
        DiffEntry(key="A", status=DiffStatus.MATCH, source_value="1", target_value="1"),
        DiffEntry(key="B", status=DiffStatus.MATCH, source_value="2", target_value="2"),
        DiffEntry(key="C", status=DiffStatus.MISMATCH, source_value="x", target_value="y"),
        DiffEntry(key="D", status=DiffStatus.MISSING_IN_TARGET, source_value="v", target_value=None),
        DiffEntry(key="E", status=DiffStatus.MISSING_IN_SOURCE, source_value=None, target_value="w"),
    ]
    return DiffResult(source="dev", target="prod", entries=entries)


def test_summarize_returns_diff_summary(result):
    summary = summarize(result)
    assert isinstance(summary, DiffSummary)


def test_summarize_source_and_target(result):
    summary = summarize(result)
    assert summary.source == "dev"
    assert summary.target == "prod"


def test_summarize_total(result):
    summary = summarize(result)
    assert summary.total == 5


def test_summarize_match_count(result):
    summary = summarize(result)
    assert summary.match_count == 2


def test_summarize_mismatch_count(result):
    summary = summarize(result)
    assert summary.mismatch_count == 1


def test_summarize_missing_in_target_count(result):
    summary = summarize(result)
    assert summary.missing_in_target_count == 1


def test_summarize_missing_in_source_count(result):
    summary = summarize(result)
    assert summary.missing_in_source_count == 1


def test_has_issues_true(result):
    summary = summarize(result)
    assert summary.has_issues is True


def test_has_issues_false():
    entries = [
        DiffEntry(key="A", status=DiffStatus.MATCH, source_value="1", target_value="1"),
    ]
    result = DiffResult(source="dev", target="prod", entries=entries)
    summary = summarize(result)
    assert summary.has_issues is False


def test_as_dict_keys(result):
    summary = summarize(result)
    d = summary.as_dict()
    assert set(d.keys()) == {"source", "target", "total", "match", "missing_in_target", "missing_in_source", "mismatch", "has_issues"}


def test_format_summary_contains_source_and_target(result):
    summary = summarize(result)
    text = format_summary(summary)
    assert "dev" in text
    assert "prod" in text


def test_format_summary_contains_counts(result):
    summary = summarize(result)
    text = format_summary(summary)
    assert "5" in text
    assert "2" in text
