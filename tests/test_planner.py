"""Tests for envdiff.planner."""
import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.planner import PlanAction, PlanResult, PlanStep, plan_reconciliation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(key: str, status: DiffStatus, src=None, tgt=None) -> DiffEntry:
    return DiffEntry(key=key, status=status, source_value=src, target_value=tgt)


@pytest.fixture()
def diff() -> DiffResult:
    return DiffResult(
        source_name=".env.production",
        target_name=".env.staging",
        entries=[
            _entry("DB_HOST", DiffStatus.MATCH, "db.prod", "db.prod"),
            _entry("API_KEY", DiffStatus.MISSING_IN_TARGET, "secret", None),
            _entry("OLD_FLAG", DiffStatus.MISSING_IN_SOURCE, None, "1"),
            _entry("PORT", DiffStatus.MISMATCH, "5432", "3306"),
        ],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_plan_returns_plan_result(diff):
    result = plan_reconciliation(diff)
    assert isinstance(result, PlanResult)


def test_plan_stores_source_and_target_names(diff):
    result = plan_reconciliation(diff)
    assert result.source_name == ".env.production"
    assert result.target_name == ".env.staging"


def test_plan_step_count_matches_entries(diff):
    result = plan_reconciliation(diff)
    assert len(result.steps) == len(diff.entries)


def test_plan_steps_are_sorted_by_key(diff):
    result = plan_reconciliation(diff)
    keys = [s.key for s in result.steps]
    assert keys == sorted(keys)


def test_match_maps_to_keep(diff):
    result = plan_reconciliation(diff)
    keep_steps = result.steps_for_action(PlanAction.KEEP)
    assert any(s.key == "DB_HOST" for s in keep_steps)


def test_missing_in_target_maps_to_add(diff):
    result = plan_reconciliation(diff)
    add_steps = result.steps_for_action(PlanAction.ADD)
    assert any(s.key == "API_KEY" for s in add_steps)


def test_missing_in_source_maps_to_remove(diff):
    result = plan_reconciliation(diff)
    remove_steps = result.steps_for_action(PlanAction.REMOVE)
    assert any(s.key == "OLD_FLAG" for s in remove_steps)


def test_mismatch_maps_to_update(diff):
    result = plan_reconciliation(diff)
    update_steps = result.steps_for_action(PlanAction.UPDATE)
    assert any(s.key == "PORT" for s in update_steps)


def test_action_count_excludes_keep(diff):
    result = plan_reconciliation(diff)
    # 3 non-KEEP entries: ADD, REMOVE, UPDATE
    assert result.action_count == 3


def test_is_noop_false_when_issues(diff):
    result = plan_reconciliation(diff)
    assert result.is_noop is False


def test_is_noop_true_when_all_match():
    all_match = DiffResult(
        source_name="a",
        target_name="b",
        entries=[
            _entry("X", DiffStatus.MATCH, "1", "1"),
            _entry("Y", DiffStatus.MATCH, "2", "2"),
        ],
    )
    result = plan_reconciliation(all_match)
    assert result.is_noop is True


def test_plan_step_values_preserved(diff):
    result = plan_reconciliation(diff)
    port_step = next(s for s in result.steps if s.key == "PORT")
    assert port_step.source_value == "5432"
    assert port_step.target_value == "3306"
