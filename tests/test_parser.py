"""Tests for the .env file parser."""

import pytest
from pathlib import Path

from envdiff.parser import parse_env_file


@pytest.fixture
def tmp_env_file(tmp_path):
    """Helper to create a temporary .env file with given content."""
    def _create(content: str) -> Path:
        env_file = tmp_path / ".env"
        env_file.write_text(content, encoding="utf-8")
        return env_file
    return _create


def test_parse_simple_key_value(tmp_env_file):
    path = tmp_env_file("KEY=value\n")
    result = parse_env_file(path)
    assert result == {"KEY": "value"}


def test_parse_multiple_entries(tmp_env_file):
    path = tmp_env_file("FOO=bar\nBAZ=qux\n")
    result = parse_env_file(path)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_ignores_comments(tmp_env_file):
    path = tmp_env_file("# This is a comment\nKEY=value\n")
    result = parse_env_file(path)
    assert result == {"KEY": "value"}


def test_parse_ignores_empty_lines(tmp_env_file):
    path = tmp_env_file("\nKEY=value\n\n")
    result = parse_env_file(path)
    assert result == {"KEY": "value"}


def test_parse_double_quoted_value(tmp_env_file):
    path = tmp_env_file('KEY="hello world"\n')
    result = parse_env_file(path)
    assert result == {"KEY": "hello world"}


def test_parse_single_quoted_value(tmp_env_file):
    path = tmp_env_file("KEY='hello world'\n")
    result = parse_env_file(path)
    assert result == {"KEY": "hello world"}


def test_parse_empty_value(tmp_env_file):
    path = tmp_env_file("KEY=\n")
    result = parse_env_file(path)
    assert result == {"KEY": None}


def test_parse_key_without_equals(tmp_env_file):
    path = tmp_env_file("BARE_KEY\n")
    result = parse_env_file(path)
    assert result == {"BARE_KEY": None}


def test_parse_value_with_equals_sign(tmp_env_file):
    path = tmp_env_file("KEY=val=ue\n")
    result = parse_env_file(path)
    assert result == {"KEY": "val=ue"}


def test_file_not_found_raises():
    with pytest.raises(FileNotFoundError):
        parse_env_file("/nonexistent/path/.env")
