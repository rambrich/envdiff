"""Tests for envdiff.tracker."""
import pytest
from envdiff.tracker import (
    ChangeType,
    TrackedChange,
    TrackResult,
    track_changes,
)


@pytest.fixture()
def old_env():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc"}


@pytest.fixture()
def new_env():
    return {"DB_HOST": "prod.db", "DB_PORT": "5432", "API_KEY": "xyz"}


@pytest.fixture()
def result(old_env, new_env):
    return track_changes(old_env, new_env, env_name="production")


def test_track_changes_returns_track_result(result):
    assert isinstance(result, TrackResult)


def test_track_changes_env_name_stored(result):
    assert result.env_name == "production"


def test_track_changes_detects_added_key(result):
    added = [c for c in result.changes if c.change_type == ChangeType.ADDED]
    assert any(c.key == "API_KEY" for c in added)


def test_track_changes_detects_removed_key(result):
    removed = [c for c in result.changes if c.change_type == ChangeType.REMOVED]
    assert any(c.key == "SECRET" for c in removed)


def test_track_changes_detects_modified_key(result):
    modified = [c for c in result.changes if c.change_type == ChangeType.MODIFIED]
    assert any(c.key == "DB_HOST" for c in modified)


def test_track_changes_detects_unchanged_key(result):
    unchanged = [c for c in result.changes if c.change_type == ChangeType.UNCHANGED]
    assert any(c.key == "DB_PORT" for c in unchanged)


def test_added_count(result):
    assert result.added_count == 1


def test_removed_count(result):
    assert result.removed_count == 1


def test_modified_count(result):
    assert result.modified_count == 1


def test_unchanged_count(result):
    assert result.unchanged_count == 1


def test_has_changes_true_when_differences(result):
    assert result.has_changes is True


def test_has_changes_false_when_identical():
    env = {"KEY": "val"}
    r = track_changes(env, env, env_name="same")
    assert r.has_changes is False


def test_added_change_has_none_old_value(result):
    added = next(c for c in result.changes if c.key == "API_KEY")
    assert added.old_value is None
    assert added.new_value == "xyz"


def test_removed_change_has_none_new_value(result):
    removed = next(c for c in result.changes if c.key == "SECRET")
    assert removed.new_value is None
    assert removed.old_value == "abc"


def test_all_keys_covered(old_env, new_env, result):
    all_keys = set(old_env) | set(new_env)
    result_keys = {c.key for c in result.changes}
    assert result_keys == all_keys


def test_empty_envs_produce_no_changes():
    r = track_changes({}, {}, env_name="empty")
    assert r.changes == []
    assert r.has_changes is False
