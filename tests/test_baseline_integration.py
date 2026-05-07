"""Integration tests: save a baseline from a file, mutate env, compare."""

import pytest
from pathlib import Path

from envdiff.baseline import Baseline, save_baseline, load_baseline, compare_to_baseline
from envdiff.parser import parse_env_file
from envdiff.differ import DiffStatus


@pytest.fixture
def env_path(tmp_path) -> Path:
    p = tmp_path / ".env.production"
    p.write_text(
        "APP_ENV=production\nDB_URL=postgres://prod/db\nFEATURE_X=true\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def saved_baseline(tmp_path, env_path) -> tuple[Baseline, Path]:
    env = parse_env_file(env_path)
    bl = Baseline(name="production", env=env)
    bl_path = tmp_path / "prod_baseline.json"
    save_baseline(bl, bl_path)
    return bl, bl_path


def test_full_round_trip_no_issues(saved_baseline, env_path):
    bl, bl_path = saved_baseline
    loaded = load_baseline(bl_path)
    current = parse_env_file(env_path)
    result = compare_to_baseline(loaded, current)
    assert not result.has_issues()


def test_full_round_trip_detects_added_key(saved_baseline, tmp_path):
    bl, bl_path = saved_baseline
    new_env_path = tmp_path / ".env.staging"
    new_env_path.write_text(
        "APP_ENV=staging\nDB_URL=postgres://prod/db\nFEATURE_X=true\nNEW_KEY=hello\n",
        encoding="utf-8",
    )
    loaded = load_baseline(bl_path)
    current = parse_env_file(new_env_path)
    result = compare_to_baseline(loaded, current, current_name="staging")
    extra_keys = {e.key for e in result.entries if e.status == DiffStatus.MISSING_IN_SOURCE}
    assert "NEW_KEY" in extra_keys


def test_full_round_trip_detects_removed_key(saved_baseline, tmp_path):
    bl, bl_path = saved_baseline
    new_env_path = tmp_path / ".env.minimal"
    new_env_path.write_text("APP_ENV=production\n", encoding="utf-8")
    loaded = load_baseline(bl_path)
    current = parse_env_file(new_env_path)
    result = compare_to_baseline(loaded, current)
    missing_keys = {e.key for e in result.entries if e.status == DiffStatus.MISSING_IN_TARGET}
    assert "DB_URL" in missing_keys
    assert "FEATURE_X" in missing_keys


def test_full_round_trip_detects_value_change(saved_baseline, tmp_path):
    bl, bl_path = saved_baseline
    new_env_path = tmp_path / ".env.changed"
    new_env_path.write_text(
        "APP_ENV=staging\nDB_URL=postgres://staging/db\nFEATURE_X=false\n",
        encoding="utf-8",
    )
    loaded = load_baseline(bl_path)
    current = parse_env_file(new_env_path)
    result = compare_to_baseline(loaded, current, current_name="staging")
    mismatch_keys = {e.key for e in result.entries if e.status == DiffStatus.MISMATCH}
    assert "APP_ENV" in mismatch_keys
    assert "DB_URL" in mismatch_keys
    assert "FEATURE_X" in mismatch_keys
