"""Tests for envdiff.auditor."""
from __future__ import annotations

import pytest

from envdiff.auditor import AuditEntry, AuditLog, audit_diff_result
from envdiff.differ import DiffEntry, DiffResult, DiffStatus


def _entry(key, status, sv=None, tv=None):
    return DiffEntry(key=key, status=status, source_value=sv, target_value=tv)


@pytest.fixture()
def diff():
    entries = [
        _entry("MATCH_KEY", DiffStatus.MATCH, "val", "val"),
        _entry("MISSING_TARGET", DiffStatus.MISSING_IN_TARGET, "val", None),
        _entry("MISSING_SOURCE", DiffStatus.MISSING_IN_SOURCE, None, "val"),
        _entry("MISMATCH_KEY", DiffStatus.VALUE_MISMATCH, "old", "new"),
    ]
    return DiffResult(source_name="src", target_name="tgt", entries=entries)


def test_audit_returns_audit_log(diff):
    log = audit_diff_result(diff, env_name="test-audit")
    assert isinstance(log, AuditLog)


def test_audit_log_env_name(diff):
    log = audit_diff_result(diff, env_name="my-env")
    assert log.env_name == "my-env"


def test_audit_log_entry_count_matches_diff(diff):
    log = audit_diff_result(diff)
    assert log.entry_count == len(diff.entries)


def test_audit_entries_are_audit_entry_instances(diff):
    log = audit_diff_result(diff)
    for e in log.entries:
        assert isinstance(e, AuditEntry)


def test_audit_entry_has_timestamp(diff):
    log = audit_diff_result(diff)
    for e in log.entries:
        assert e.timestamp  # non-empty ISO string


def test_audit_operation_match(diff):
    log = audit_diff_result(diff)
    match_entries = log.for_operation("match")
    assert len(match_entries) == 1
    assert match_entries[0].key == "MATCH_KEY"


def test_audit_operation_missing_in_target(diff):
    log = audit_diff_result(diff)
    entries = log.for_operation("missing_in_target")
    assert len(entries) == 1
    assert entries[0].key == "MISSING_TARGET"


def test_audit_operation_missing_in_source(diff):
    log = audit_diff_result(diff)
    entries = log.for_operation("missing_in_source")
    assert len(entries) == 1
    assert entries[0].key == "MISSING_SOURCE"


def test_audit_operation_value_mismatch(diff):
    log = audit_diff_result(diff)
    entries = log.for_operation("value_mismatch")
    assert len(entries) == 1
    assert entries[0].key == "MISMATCH_KEY"


def test_audit_mismatch_detail_contains_values(diff):
    log = audit_diff_result(diff)
    mismatch = log.for_key("MISMATCH_KEY")[0]
    assert "old" in mismatch.detail
    assert "new" in mismatch.detail


def test_audit_source_and_target_stored(diff):
    log = audit_diff_result(diff)
    for e in log.entries:
        assert e.source == "src"
        assert e.target == "tgt"


def test_audit_for_key_returns_entries(diff):
    log = audit_diff_result(diff)
    entries = log.for_key("MATCH_KEY")
    assert len(entries) == 1


def test_audit_for_key_unknown_returns_empty(diff):
    log = audit_diff_result(diff)
    assert log.for_key("DOES_NOT_EXIST") == []


def test_audit_empty_diff():
    empty = DiffResult(source_name="a", target_name="b", entries=[])
    log = audit_diff_result(empty)
    assert log.entry_count == 0
