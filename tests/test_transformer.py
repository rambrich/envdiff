"""Tests for envdiff.transformer."""
import pytest

from envdiff.transformer import (
    TransformOp,
    TransformRecord,
    TransformResult,
    transform_env,
)


@pytest.fixture()
def sample_env():
    return {
        "APP_HOST": "localhost",
        "APP_PORT": "8080",
        "DEBUG": "true",
    }


# --- TransformResult helpers ---

def test_transform_result_changed_count(sample_env):
    result = transform_env(sample_env, TransformOp.ADD_PREFIX, prefix="NEW_")
    assert result.changed_count == 3


def test_transform_result_output_env_keys(sample_env):
    result = transform_env(sample_env, TransformOp.ADD_PREFIX, prefix="X_")
    assert set(result.output_env.keys()) == {"X_APP_HOST", "X_APP_PORT", "X_DEBUG"}


def test_transform_result_output_env_values_preserved(sample_env):
    result = transform_env(sample_env, TransformOp.ADD_PREFIX, prefix="X_")
    assert result.output_env["X_APP_HOST"] == "localhost"


def test_transform_result_env_name():
    result = transform_env({}, TransformOp.TO_UPPER, env_name="production")
    assert result.env_name == "production"


# --- ADD_PREFIX ---

def test_add_prefix_renames_keys(sample_env):
    result = transform_env(sample_env, TransformOp.ADD_PREFIX, prefix="PRE_")
    new_keys = {r.new_key for r in result.records}
    assert "PRE_APP_HOST" in new_keys


def test_add_prefix_marks_changed(sample_env):
    result = transform_env(sample_env, TransformOp.ADD_PREFIX, prefix="PRE_")
    assert all(r.changed for r in result.records)


# --- REMOVE_PREFIX ---

def test_remove_prefix_strips_known_prefix():
    env = {"APP_HOST": "localhost", "APP_PORT": "8080"}
    result = transform_env(env, TransformOp.REMOVE_PREFIX, prefix="APP_")
    new_keys = {r.new_key for r in result.records}
    assert new_keys == {"HOST", "PORT"}


def test_remove_prefix_no_match_leaves_key_unchanged():
    env = {"OTHER_KEY": "val"}
    result = transform_env(env, TransformOp.REMOVE_PREFIX, prefix="APP_")
    assert result.records[0].changed is False


# --- TO_UPPER / TO_LOWER ---

def test_to_upper_converts_keys():
    env = {"app_host": "localhost"}
    result = transform_env(env, TransformOp.TO_UPPER)
    assert result.records[0].new_key == "APP_HOST"


def test_to_lower_converts_keys(sample_env):
    result = transform_env(sample_env, TransformOp.TO_LOWER)
    new_keys = {r.new_key for r in result.records}
    assert "app_host" in new_keys and "debug" in new_keys


def test_already_upper_not_changed():
    env = {"APP_HOST": "v"}
    result = transform_env(env, TransformOp.TO_UPPER)
    assert result.records[0].changed is False


# --- SET_VALUE ---

def test_set_value_replaces_all_values(sample_env):
    result = transform_env(sample_env, TransformOp.SET_VALUE, value="REDACTED")
    assert all(r.new_value == "REDACTED" for r in result.records)


def test_set_value_marks_changed_when_different(sample_env):
    result = transform_env(sample_env, TransformOp.SET_VALUE, value="REDACTED")
    assert all(r.changed for r in result.records)


# --- keys filter ---

def test_keys_filter_only_transforms_specified(sample_env):
    result = transform_env(
        sample_env, TransformOp.ADD_PREFIX, prefix="Z_", keys=["DEBUG"]
    )
    changed = [r for r in result.records if r.changed]
    assert len(changed) == 1
    assert changed[0].new_key == "Z_DEBUG"


def test_keys_filter_leaves_others_untouched(sample_env):
    result = transform_env(
        sample_env, TransformOp.ADD_PREFIX, prefix="Z_", keys=["DEBUG"]
    )
    unchanged = [r for r in result.records if not r.changed]
    assert {r.key for r in unchanged} == {"APP_HOST", "APP_PORT"}
