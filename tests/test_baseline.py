"""Tests for envdiff.baseline module."""

import json
import pytest
from pathlib import Path

from envdiff.baseline import Baseline, save_baseline, load_baseline, compare_to_baseline
from envdiff.differ import DiffResult, DiffStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_env() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc"}


@pytest.fixture
def baseline(sample_env) -> Baseline:
    return Baseline(name="production", env=sample_env, description="prod snapshot")


@pytest.fixture
def baseline_file(tmp_path, baseline) -> Path:
    p = tmp_path / "baseline.json"
    save_baseline(baseline, p)
    return p


# ---------------------------------------------------------------------------
# Baseline dataclass
# ---------------------------------------------------------------------------

def test_baseline_to_dict(baseline):
    d = baseline.to_dict()
    assert d["name"] == "production"
    assert d["env"]["DB_HOST"] == "localhost"
    assert d["description"] == "prod snapshot"


def test_baseline_from_dict(baseline):
    restored = Baseline.from_dict(baseline.to_dict())
    assert restored.name == baseline.name
    assert restored.env == baseline.env
    assert restored.description == baseline.description


def test_baseline_default_description():
    b = Baseline(name="dev", env={"K": "V"})
    assert b.description == ""


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------

def test_save_baseline_creates_file(tmp_path, baseline):
    p = tmp_path / "snap.json"
    save_baseline(baseline, p)
    assert p.exists()


def test_save_baseline_valid_json(tmp_path, baseline):
    p = tmp_path / "snap.json"
    save_baseline(baseline, p)
    data = json.loads(p.read_text())
    assert data["name"] == "production"


def test_load_baseline_round_trip(baseline_file, baseline):
    loaded = load_baseline(baseline_file)
    assert loaded.name == baseline.name
    assert loaded.env == baseline.env
    assert loaded.description == baseline.description


# ---------------------------------------------------------------------------
# compare_to_baseline
# ---------------------------------------------------------------------------

def test_compare_returns_diff_result(baseline, sample_env):
    result = compare_to_baseline(baseline, sample_env)
    assert isinstance(result, DiffResult)


def test_compare_no_issues_when_identical(baseline, sample_env):
    result = compare_to_baseline(baseline, sample_env)
    assert not result.has_issues()


def test_compare_detects_missing_in_current(baseline):
    current = {"DB_HOST": "localhost"}  # missing DB_PORT and SECRET
    result = compare_to_baseline(baseline, current)
    missing_keys = {e.key for e in result.entries if e.status == DiffStatus.MISSING_IN_TARGET}
    assert "DB_PORT" in missing_keys
    assert "SECRET" in missing_keys


def test_compare_detects_value_mismatch(baseline):
    current = {"DB_HOST": "remotehost", "DB_PORT": "5432", "SECRET": "abc"}
    result = compare_to_baseline(baseline, current)
    mismatch_keys = {e.key for e in result.entries if e.status == DiffStatus.MISMATCH}
    assert "DB_HOST" in mismatch_keys


def test_compare_source_name_is_baseline_name(baseline, sample_env):
    result = compare_to_baseline(baseline, sample_env)
    assert result.source_name == "production"


def test_compare_target_name_default(baseline, sample_env):
    result = compare_to_baseline(baseline, sample_env)
    assert result.target_name == "current"


def test_compare_target_name_custom(baseline, sample_env):
    result = compare_to_baseline(baseline, sample_env, current_name="staging")
    assert result.target_name == "staging"
