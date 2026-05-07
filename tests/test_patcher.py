"""Tests for envdiff.patcher."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffResult, diff_envs
from envdiff.patcher import PatchAction, patch_env


@pytest.fixture()
def source() -> dict:
    return {"A": "1", "B": "2", "C": "3"}


@pytest.fixture()
def target() -> dict:
    # Missing C, B has different value
    return {"A": "1", "B": "99"}


@pytest.fixture()
def diff(source, target) -> DiffResult:
    return diff_envs(source, target, source_name="source", target_name="target")


# ---------------------------------------------------------------------------
# patch_env — apply_missing=True (default), apply_mismatch=False (default)
# ---------------------------------------------------------------------------

def test_patch_adds_missing_key(source, target, diff):
    result = patch_env(target, diff)
    assert result.patched_env["C"] == "3"


def test_patch_does_not_change_existing_match(source, target, diff):
    result = patch_env(target, diff)
    assert result.patched_env["A"] == "1"


def test_patch_does_not_overwrite_mismatch_by_default(source, target, diff):
    result = patch_env(target, diff)
    assert result.patched_env["B"] == "99"


def test_patch_record_added_action(source, target, diff):
    result = patch_env(target, diff)
    added = [r for r in result.records if r.action == PatchAction.ADDED]
    assert len(added) == 1
    assert added[0].key == "C"
    assert added[0].new_value == "3"
    assert added[0].old_value is None


def test_patch_record_skipped_mismatch_by_default(source, target, diff):
    result = patch_env(target, diff)
    skipped = [r for r in result.records if r.action == PatchAction.SKIPPED]
    assert any(r.key == "B" for r in skipped)


# ---------------------------------------------------------------------------
# patch_env — apply_mismatch=True
# ---------------------------------------------------------------------------

def test_patch_overwrites_mismatch_when_flag_set(source, target, diff):
    result = patch_env(target, diff, apply_mismatch=True)
    assert result.patched_env["B"] == "2"


def test_patch_record_updated_action(source, target, diff):
    result = patch_env(target, diff, apply_mismatch=True)
    updated = [r for r in result.records if r.action == PatchAction.UPDATED]
    assert len(updated) == 1
    assert updated[0].key == "B"
    assert updated[0].old_value == "99"
    assert updated[0].new_value == "2"


# ---------------------------------------------------------------------------
# patch_env — apply_missing=False
# ---------------------------------------------------------------------------

def test_patch_skips_missing_when_flag_false(source, target, diff):
    result = patch_env(target, diff, apply_missing=False)
    assert "C" not in result.patched_env


def test_patch_skipped_count(source, target, diff):
    result = patch_env(target, diff, apply_missing=False)
    assert result.skipped_count >= 1


# ---------------------------------------------------------------------------
# applied_count / skipped_count helpers
# ---------------------------------------------------------------------------

def test_applied_count_reflects_changes(source, target, diff):
    result = patch_env(target, diff, apply_missing=True, apply_mismatch=True)
    assert result.applied_count == 2  # C added + B updated


def test_original_dict_not_mutated(source, target, diff):
    original_keys = set(target.keys())
    patch_env(target, diff)
    assert set(target.keys()) == original_keys
