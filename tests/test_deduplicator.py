"""Tests for envdiff.deduplicator."""
import pytest

from envdiff.deduplicator import (
    DedupeStrategy,
    DedupeRecord,
    DedupeResult,
    deduplicate,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _pairs(*items):
    """Build a list of (key, value) tuples from alternating args."""
    it = iter(items)
    return list(zip(it, it))


# ---------------------------------------------------------------------------
# DedupeResult properties
# ---------------------------------------------------------------------------

def test_dedupe_result_is_clean_when_no_records():
    result = DedupeResult(env_name="test", output_env={"A": "1"})
    assert result.is_clean is True


def test_dedupe_result_not_clean_when_records():
    rec = DedupeRecord(key="A", kept_value="1", discarded_values=["2"])
    result = DedupeResult(env_name="test", output_env={"A": "1"}, records=[rec])
    assert result.is_clean is False
    assert result.deduped_count == 1


# ---------------------------------------------------------------------------
# deduplicate — no duplicates
# ---------------------------------------------------------------------------

def test_deduplicate_no_duplicates_returns_clean_result():
    pairs = _pairs("A", "1", "B", "2")
    result = deduplicate(pairs, env_name="dev")
    assert result.is_clean is True
    assert result.output_env == {"A": "1", "B": "2"}


def test_deduplicate_env_name_stored():
    result = deduplicate([], env_name="staging")
    assert result.env_name == "staging"


def test_deduplicate_empty_pairs():
    result = deduplicate([])
    assert result.output_env == {}
    assert result.is_clean is True


# ---------------------------------------------------------------------------
# deduplicate — FIRST strategy
# ---------------------------------------------------------------------------

def test_deduplicate_first_keeps_first_value():
    pairs = _pairs("KEY", "first", "KEY", "second", "KEY", "third")
    result = deduplicate(pairs, strategy=DedupeStrategy.FIRST)
    assert result.output_env["KEY"] == "first"


def test_deduplicate_first_records_discarded():
    pairs = _pairs("KEY", "first", "KEY", "second")
    result = deduplicate(pairs, strategy=DedupeStrategy.FIRST)
    assert result.records[0].discarded_values == ["second"]


def test_deduplicate_first_deduped_count():
    pairs = _pairs("A", "1", "A", "2", "B", "3", "B", "4")
    result = deduplicate(pairs, strategy=DedupeStrategy.FIRST)
    assert result.deduped_count == 2


# ---------------------------------------------------------------------------
# deduplicate — LAST strategy
# ---------------------------------------------------------------------------

def test_deduplicate_last_keeps_last_value():
    pairs = _pairs("KEY", "first", "KEY", "second", "KEY", "third")
    result = deduplicate(pairs, strategy=DedupeStrategy.LAST)
    assert result.output_env["KEY"] == "third"


def test_deduplicate_last_records_discarded():
    pairs = _pairs("KEY", "first", "KEY", "second")
    result = deduplicate(pairs, strategy=DedupeStrategy.LAST)
    assert result.records[0].discarded_values == ["first"]


# ---------------------------------------------------------------------------
# deduplicate — ERROR strategy
# ---------------------------------------------------------------------------

def test_deduplicate_error_raises_on_duplicate():
    pairs = _pairs("KEY", "a", "KEY", "b")
    with pytest.raises(ValueError, match="KEY"):
        deduplicate(pairs, strategy=DedupeStrategy.ERROR)


def test_deduplicate_error_passes_when_no_duplicates():
    pairs = _pairs("A", "1", "B", "2")
    result = deduplicate(pairs, strategy=DedupeStrategy.ERROR)
    assert result.is_clean is True


# ---------------------------------------------------------------------------
# key ordering preserved
# ---------------------------------------------------------------------------

def test_deduplicate_preserves_insertion_order():
    pairs = _pairs("Z", "1", "A", "2", "M", "3")
    result = deduplicate(pairs)
    assert list(result.output_env.keys()) == ["Z", "A", "M"]
