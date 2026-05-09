"""Tests for envdiff.duplicates."""
from pathlib import Path

import pytest

from envdiff.duplicates import DuplicateEntry, DuplicateResult, find_duplicates


@pytest.fixture()
def tmp_env(tmp_path: Path):
    """Return a factory that writes content to a temp .env file."""

    def _write(text: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(text, encoding="utf-8")
        return p

    return _write


# ---------------------------------------------------------------------------
# DuplicateResult helpers
# ---------------------------------------------------------------------------

def test_has_duplicates_false_when_empty():
    result = DuplicateResult(env_name="test")
    assert result.has_duplicates is False


def test_has_duplicates_true_when_entries():
    entry = DuplicateEntry(key="FOO", line_numbers=[1, 3], values=["a", "b"])
    result = DuplicateResult(env_name="test", duplicates=[entry])
    assert result.has_duplicates is True


def test_duplicate_count():
    entries = [
        DuplicateEntry(key="A", line_numbers=[1, 2], values=["x", "y"]),
        DuplicateEntry(key="B", line_numbers=[3, 5], values=["p", "q"]),
    ]
    result = DuplicateResult(env_name="test", duplicates=entries)
    assert result.duplicate_count == 2


def test_entry_count_property():
    entry = DuplicateEntry(key="FOO", line_numbers=[1, 4, 7], values=["a", "b", "c"])
    assert entry.count == 3


# ---------------------------------------------------------------------------
# find_duplicates
# ---------------------------------------------------------------------------

def test_no_duplicates_clean_file(tmp_env):
    p = tmp_env("FOO=bar\nBAZ=qux\n")
    result = find_duplicates(p)
    assert result.has_duplicates is False
    assert result.duplicates == []


def test_detects_single_duplicate_key(tmp_env):
    p = tmp_env("FOO=first\nBAR=ok\nFOO=second\n")
    result = find_duplicates(p)
    assert result.has_duplicates is True
    assert len(result.duplicates) == 1
    dup = result.duplicates[0]
    assert dup.key == "FOO"
    assert dup.line_numbers == [1, 3]
    assert dup.values == ["first", "second"]


def test_detects_multiple_duplicate_keys(tmp_env):
    p = tmp_env("A=1\nB=2\nA=3\nB=4\n")
    result = find_duplicates(p)
    keys = {d.key for d in result.duplicates}
    assert keys == {"A", "B"}


def test_ignores_comments_and_blank_lines(tmp_env):
    content = "# comment\n\nFOO=bar\n# another\nFOO=baz\n"
    p = tmp_env(content)
    result = find_duplicates(p)
    assert result.has_duplicates is True
    assert result.duplicates[0].line_numbers == [3, 5]


def test_env_name_defaults_to_filename(tmp_env):
    p = tmp_env("X=1\n")
    result = find_duplicates(p)
    assert result.env_name == ".env"


def test_env_name_override(tmp_env):
    p = tmp_env("X=1\n")
    result = find_duplicates(p, env_name="production")
    assert result.env_name == "production"


def test_quoted_values_are_stripped(tmp_env):
    p = tmp_env('SECRET="hello"\nSECRET="world"\n')
    result = find_duplicates(p)
    assert result.duplicates[0].values == ["hello", "world"]


def test_triplicate_key(tmp_env):
    p = tmp_env("KEY=a\nKEY=b\nKEY=c\n")
    result = find_duplicates(p)
    dup = result.duplicates[0]
    assert dup.count == 3
    assert dup.line_numbers == [1, 2, 3]
