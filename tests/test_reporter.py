"""Tests for envdiff.reporter module."""

import io
import pytest
from envdiff.differ import diff_envs
from envdiff.reporter import format_report, print_report


SOURCE = {"DB_HOST": "localhost", "SECRET": "abc", "SHARED": "same"}
TARGET = {"DB_HOST": "prod.host", "API_KEY": "xyz", "SHARED": "same"}


@pytest.fixture
def result():
    return diff_envs(SOURCE, TARGET, source_name="dev", target_name="prod")


def test_format_report_contains_header(result):
    report = format_report(result)
    assert "dev" in report
    assert "prod" in report


def test_format_report_shows_missing_in_target(result):
    report = format_report(result)
    assert "SECRET" in report
    assert "MISSING IN TARGET" in report


def test_format_report_shows_missing_in_source(result):
    report = format_report(result)
    assert "API_KEY" in report
    assert "MISSING IN SOURCE" in report


def test_format_report_shows_mismatch(result):
    report = format_report(result)
    assert "DB_HOST" in report
    assert "MISMATCH" in report


def test_format_report_hides_ok_by_default(result):
    report = format_report(result)
    assert "SHARED" not in report


def test_format_report_shows_ok_when_requested(result):
    report = format_report(result, show_ok=True)
    assert "SHARED" in report
    assert "OK" in report


def test_format_report_summary_line(result):
    report = format_report(result)
    assert "Summary:" in report


def test_format_report_summary_all_match():
    env = {"KEY": "value"}
    result = diff_envs(env, env)
    report = format_report(result)
    assert "all keys match" in report


def test_print_report_writes_to_stream(result):
    buf = io.StringIO()
    print_report(result, file=buf)
    output = buf.getvalue()
    assert len(output) > 0
    assert "dev" in output


def test_mismatch_shows_both_values(result):
    report = format_report(result)
    assert "localhost" in report
    assert "prod.host" in report
