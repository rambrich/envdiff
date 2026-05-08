"""Tests for envdiff.renamer."""
import pytest
from envdiff.renamer import RenameRecord, RenameResult, rename_keys


@pytest.fixture()
def base_env():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_SECRET": "s3cr3t"}


def test_rename_returns_rename_result(base_env):
    result = rename_keys(base_env, {"DB_HOST": "DATABASE_HOST"})
    assert isinstance(result, RenameResult)


def test_rename_applied_count(base_env):
    result = rename_keys(base_env, {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"})
    assert result.applied_count == 2


def test_rename_skipped_count_for_missing_key(base_env):
    result = rename_keys(base_env, {"MISSING_KEY": "NEW_KEY"})
    assert result.skipped_count == 1
    assert result.applied_count == 0


def test_rename_removes_old_key_by_default(base_env):
    result = rename_keys(base_env, {"DB_HOST": "DATABASE_HOST"})
    assert "DB_HOST" not in result.renamed
    assert "DATABASE_HOST" in result.renamed


def test_rename_keeps_old_key_when_remove_old_false(base_env):
    result = rename_keys(base_env, {"DB_HOST": "DATABASE_HOST"}, remove_old=False)
    assert "DB_HOST" in result.renamed
    assert "DATABASE_HOST" in result.renamed


def test_rename_preserves_value(base_env):
    result = rename_keys(base_env, {"DB_HOST": "DATABASE_HOST"})
    assert result.renamed["DATABASE_HOST"] == "localhost"


def test_rename_original_is_unchanged(base_env):
    original_copy = dict(base_env)
    result = rename_keys(base_env, {"DB_HOST": "DATABASE_HOST"})
    assert result.original == original_copy


def test_rename_record_applied_true_for_existing_key(base_env):
    result = rename_keys(base_env, {"DB_HOST": "DATABASE_HOST"})
    rec = result.records[0]
    assert isinstance(rec, RenameRecord)
    assert rec.applied is True
    assert rec.old_key == "DB_HOST"
    assert rec.new_key == "DATABASE_HOST"


def test_rename_record_applied_false_for_missing_key(base_env):
    result = rename_keys(base_env, {"NOPE": "ALSO_NOPE"})
    rec = result.records[0]
    assert rec.applied is False


def test_rename_unchanged_keys_preserved(base_env):
    result = rename_keys(base_env, {"DB_HOST": "DATABASE_HOST"})
    assert result.renamed["DB_PORT"] == "5432"
    assert result.renamed["APP_SECRET"] == "s3cr3t"


def test_rename_empty_mapping_returns_copy(base_env):
    result = rename_keys(base_env, {})
    assert result.renamed == base_env
    assert result.applied_count == 0


def test_rename_empty_env():
    result = rename_keys({}, {"OLD": "NEW"})
    assert result.renamed == {}
    assert result.skipped_count == 1
