"""Tests for envdiff.tagger and envdiff.cli_tagger."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from envdiff.tagger import TagRule, TaggedKey, TagResult, tag_env
from envdiff.cli_tagger import main


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_SECRET": "s3cr3t",
        "APP_DEBUG": "true",
        "UNRELATED": "value",
    }


@pytest.fixture()
def basic_rules() -> list:
    return [
        TagRule(tag="database", pattern="DB_*"),
        TagRule(tag="app", pattern="APP_*"),
    ]


# ---------------------------------------------------------------------------
# tag_env unit tests
# ---------------------------------------------------------------------------

def test_tag_env_returns_tag_result(sample_env, basic_rules):
    result = tag_env(sample_env, basic_rules)
    assert isinstance(result, TagResult)


def test_tag_env_name_stored(sample_env, basic_rules):
    result = tag_env(sample_env, basic_rules, env_name="production")
    assert result.env_name == "production"


def test_tag_env_entry_count(sample_env, basic_rules):
    result = tag_env(sample_env, basic_rules)
    assert len(result.entries) == len(sample_env)


def test_tag_env_entries_are_tagged_key(sample_env, basic_rules):
    result = tag_env(sample_env, basic_rules)
    assert all(isinstance(e, TaggedKey) for e in result.entries)


def test_tag_env_db_keys_get_database_tag(sample_env, basic_rules):
    result = tag_env(sample_env, basic_rules)
    assert "database" in result.tags_for_key("DB_HOST")
    assert "database" in result.tags_for_key("DB_PORT")


def test_tag_env_app_keys_get_app_tag(sample_env, basic_rules):
    result = tag_env(sample_env, basic_rules)
    assert "app" in result.tags_for_key("APP_SECRET")
    assert "app" in result.tags_for_key("APP_DEBUG")


def test_tag_env_unmatched_key_has_no_tags(sample_env, basic_rules):
    result = tag_env(sample_env, basic_rules)
    assert result.tags_for_key("UNRELATED") == []


def test_tag_env_untagged_label_applied(sample_env, basic_rules):
    result = tag_env(sample_env, basic_rules, untagged_label="other")
    assert "other" in result.tags_for_key("UNRELATED")


def test_tag_env_all_tags_sorted(sample_env, basic_rules):
    result = tag_env(sample_env, basic_rules)
    assert result.all_tags == sorted(result.all_tags)


def test_tag_env_keys_for_tag(sample_env, basic_rules):
    result = tag_env(sample_env, basic_rules)
    db_keys = result.keys_for_tag("database")
    assert "DB_HOST" in db_keys
    assert "DB_PORT" in db_keys


def test_tag_env_entries_sorted_alphabetically(sample_env, basic_rules):
    result = tag_env(sample_env, basic_rules)
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent("""\
        DB_HOST=localhost
        DB_PORT=5432
        APP_SECRET=s3cr3t
        UNRELATED=value
    """))
    return p


def test_cli_returns_zero(env_file):
    assert main([str(env_file), "--rule", "database:DB_*"]) == 0


def test_cli_missing_file_returns_two(tmp_path):
    assert main([str(tmp_path / "missing.env")]) == 2


def test_cli_invalid_rule_returns_two(env_file):
    assert main([str(env_file), "--rule", "BADFORMAT"]) == 2


def test_cli_json_output_is_valid(env_file, capsys):
    main([str(env_file), "--rule", "database:DB_*", "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "entries" in data
    assert "all_tags" in data


def test_cli_json_contains_expected_tag(env_file, capsys):
    main([str(env_file), "--rule", "database:DB_*", "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "database" in data["all_tags"]
