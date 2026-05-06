"""Tests for envdiff.differ module."""

import pytest
from envdiff.differ import diff_envs, DiffStatus, DiffResult


SOURCE = {
    "APP_NAME": "myapp",
    "DEBUG": "true",
    "DB_HOST": "localhost",
    "SECRET_KEY": "abc123",
}

TARGET = {
    "APP_NAME": "myapp",
    "DEBUG": "false",
    "DB_HOST": "prod.db.example.com",
    "API_KEY": "xyz789",
}


def test_diff_returns_diff_result():
    result = diff_envs(SOURCE, TARGET)
    assert isinstance(result, DiffResult)


def test_diff_source_and_target_names():
    result = diff_envs(SOURCE, TARGET, source_name="dev", target_name="prod")
    assert result.source_name == "dev"
    assert result.target_name == "prod"


def test_missing_in_target():
    result = diff_envs(SOURCE, TARGET)
    missing_keys = [e.key for e in result.missing_in_target]
    assert "SECRET_KEY" in missing_keys


def test_missing_in_source():
    result = diff_envs(SOURCE, TARGET)
    missing_keys = [e.key for e in result.missing_in_source]
    assert "API_KEY" in missing_keys


def test_value_mismatch():
    result = diff_envs(SOURCE, TARGET)
    mismatched_keys = [e.key for e in result.mismatched]
    assert "DEBUG" in mismatched_keys
    assert "DB_HOST" in mismatched_keys


def test_ok_status_for_matching_keys():
    result = diff_envs(SOURCE, TARGET)
    ok_entries = [e for e in result.entries if e.status == DiffStatus.OK]
    assert any(e.key == "APP_NAME" for e in ok_entries)


def test_has_issues_true_when_differences():
    result = diff_envs(SOURCE, TARGET)
    assert result.has_issues is True


def test_has_issues_false_when_identical():
    result = diff_envs(SOURCE, SOURCE)
    assert result.has_issues is False


def test_keys_only_skips_value_comparison():
    result = diff_envs(SOURCE, TARGET, keys_only=True)
    mismatched = result.mismatched
    assert len(mismatched) == 0


def test_empty_envs_produce_no_entries():
    result = diff_envs({}, {})
    assert result.entries == []


def test_entries_sorted_by_key():
    result = diff_envs(SOURCE, TARGET)
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_mismatch_entry_contains_both_values():
    result = diff_envs(SOURCE, TARGET)
    debug_entry = next(e for e in result.entries if e.key == "DEBUG")
    assert debug_entry.source_value == "true"
    assert debug_entry.target_value == "false"
