"""Tests for envdiff.linter module."""

import pytest
from pathlib import Path

from envdiff.linter import lint_env_file, LintSeverity, LintIssue, LintResult


@pytest.fixture
def tmp_env(tmp_path):
    """Helper: write a temp .env file and return its path string."""
    def _write(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(content)
        return str(p)
    return _write


def test_lint_clean_file_returns_no_issues(tmp_env):
    path = tmp_env("DATABASE_URL=postgres://localhost/db\nSECRET_KEY=abc123\n")
    result = lint_env_file(path)
    assert result.is_clean
    assert result.error_count == 0
    assert result.warning_count == 0


def test_lint_result_env_name_defaults_to_path(tmp_env):
    path = tmp_env("KEY=value\n")
    result = lint_env_file(path)
    assert result.env_name == path


def test_lint_result_env_name_override(tmp_env):
    path = tmp_env("KEY=value\n")
    result = lint_env_file(path, env_name="production")
    assert result.env_name == "production"


def test_lint_detects_missing_equals(tmp_env):
    path = tmp_env("NOT_VALID_LINE\n")
    result = lint_env_file(path)
    assert not result.is_clean
    assert any(i.severity == LintSeverity.ERROR for i in result.issues)
    assert any("not a valid" in i.message.lower() for i in result.issues)


def test_lint_detects_lowercase_key(tmp_env):
    path = tmp_env("my_key=value\n")
    result = lint_env_file(path)
    assert any("uppercase" in i.message.lower() for i in result.issues)
    assert any(i.severity == LintSeverity.WARNING for i in result.issues)


def test_lint_detects_whitespace_in_key(tmp_env):
    path = tmp_env(" MY_KEY=value\n")
    result = lint_env_file(path)
    assert any("whitespace" in i.message.lower() for i in result.issues)


def test_lint_detects_quoted_value(tmp_env):
    path = tmp_env('MY_KEY="some value"\n')
    result = lint_env_file(path)
    assert any("quotes" in i.message.lower() for i in result.issues)
    assert any(i.severity == LintSeverity.WARNING for i in result.issues)


def test_lint_detects_single_quoted_value(tmp_env):
    path = tmp_env("MY_KEY='some value'\n")
    result = lint_env_file(path)
    assert any("quotes" in i.message.lower() for i in result.issues)


def test_lint_ignores_comments(tmp_env):
    path = tmp_env("# This is a comment\nKEY=value\n")
    result = lint_env_file(path)
    assert result.is_clean


def test_lint_ignores_blank_lines(tmp_env):
    path = tmp_env("\n\nKEY=value\n\n")
    result = lint_env_file(path)
    assert result.is_clean


def test_lint_error_count_and_warning_count(tmp_env):
    path = tmp_env("lowercase_key=value\nNOT_VALID\nGOOD_KEY=fine\n")
    result = lint_env_file(path)
    assert result.error_count >= 1
    assert result.warning_count >= 1


def test_lint_issue_repr():
    issue = LintIssue(line_number=3, key="bad_key", message="Key is not uppercase", severity=LintSeverity.WARNING)
    r = repr(issue)
    assert "bad_key" in r
    assert "warning" in r
    assert "3" in r


def test_lint_multiple_issues_on_different_lines(tmp_env):
    path = tmp_env("bad_key=value\nanother_bad=stuff\n")
    result = lint_env_file(path)
    line_numbers = [i.line_number for i in result.issues]
    assert 1 in line_numbers
    assert 2 in line_numbers
