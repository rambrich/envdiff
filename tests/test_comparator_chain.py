"""Tests for envdiff.comparator_chain."""
from __future__ import annotations

import pytest

from envdiff.comparator_chain import ChainResult, ComparatorChain, build_chain
from envdiff.differ import DiffEntry, DiffResult, DiffStatus


def _entry(key: str, status: DiffStatus) -> DiffEntry:
    src = "dev" if status != DiffStatus.MISSING_IN_SOURCE else None
    tgt = "prod" if status != DiffStatus.MISSING_IN_TARGET else None
    return DiffEntry(key=key, status=status, source_value=src, target_value=tgt)


@pytest.fixture()
def diff_result() -> DiffResult:
    return DiffResult(
        source="dev",
        target="prod",
        entries=[
            _entry("DB_HOST", DiffStatus.MATCH),
            _entry("SECRET", DiffStatus.MISMATCH),
            _entry("API_KEY", DiffStatus.MISSING_IN_TARGET),
        ],
    )


def test_build_chain_returns_comparator_chain():
    chain = build_chain()
    assert isinstance(chain, ComparatorChain)


def test_run_with_no_steps_returns_original(diff_result):
    chain = build_chain()
    cr = chain.run(diff_result)
    assert isinstance(cr, ChainResult)
    assert cr.steps_applied == 0
    assert len(cr.result.entries) == 3


def test_run_records_step_names(diff_result):
    chain = build_chain(("identity", lambda d: d))
    cr = chain.run(diff_result)
    assert cr.step_names == ["identity"]


def test_run_applies_step(diff_result):
    # Step that keeps only MATCH entries
    def keep_match(d: DiffResult) -> DiffResult:
        return DiffResult(
            source=d.source,
            target=d.target,
            entries=[e for e in d.entries if e.status == DiffStatus.MATCH],
        )

    chain = build_chain(("keep_match", keep_match))
    cr = chain.run(diff_result)
    assert len(cr.result.entries) == 1
    assert cr.result.entries[0].key == "DB_HOST"


def test_chain_result_source_and_target(diff_result):
    chain = build_chain()
    cr = chain.run(diff_result)
    assert cr.source == "dev"
    assert cr.target == "prod"


def test_chain_result_has_issues_true(diff_result):
    chain = build_chain()
    cr = chain.run(diff_result)
    assert cr.has_issues is True


def test_chain_result_has_issues_false():
    dr = DiffResult(
        source="a",
        target="b",
        entries=[_entry("X", DiffStatus.MATCH)],
    )
    chain = build_chain()
    cr = chain.run(dr)
    assert cr.has_issues is False


def test_add_step_returns_self():
    chain = ComparatorChain()
    returned = chain.add_step("noop", lambda d: d)
    assert returned is chain


def test_multiple_steps_applied_in_order(diff_result):
    log = []

    def step_a(d):
        log.append("a")
        return d

    def step_b(d):
        log.append("b")
        return d

    chain = build_chain(("a", step_a), ("b", step_b))
    chain.run(diff_result)
    assert log == ["a", "b"]


def test_steps_applied_count(diff_result):
    chain = build_chain(
        ("s1", lambda d: d),
        ("s2", lambda d: d),
        ("s3", lambda d: d),
    )
    cr = chain.run(diff_result)
    assert cr.steps_applied == 3
