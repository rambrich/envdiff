"""Tests for envdiff.resolver."""
import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.resolver import ResolveSuggestion, ResolveResult, resolve_missing


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(key: str, status: DiffStatus, src: str = "src_val", tgt: str = "tgt_val") -> DiffEntry:
    return DiffEntry(
        key=key,
        status=status,
        source_value=src if status is not DiffStatus.MISSING_IN_SOURCE else None,
        target_value=tgt if status is not DiffStatus.MISSING_IN_TARGET else None,
    )


@pytest.fixture()
def diff() -> DiffResult:
    return DiffResult(
        source_name=".env.production",
        target_name=".env.staging",
        entries=[
            _entry("DB_HOST", DiffStatus.MATCH),
            _entry("API_KEY", DiffStatus.MISSING_IN_TARGET, src="secret", tgt=""),
            _entry("LOG_LEVEL", DiffStatus.MISSING_IN_TARGET, src="info", tgt=""),
            _entry("EXTRA", DiffStatus.MISSING_IN_SOURCE, src="", tgt="extra_val"),
            _entry("PORT", DiffStatus.MISMATCH, src="8080", tgt="9090"),
        ],
    )


# ---------------------------------------------------------------------------
# ResolveResult structure
# ---------------------------------------------------------------------------

def test_resolve_returns_resolve_result(diff):
    result = resolve_missing(diff)
    assert isinstance(result, ResolveResult)


def test_resolve_source_and_target_names(diff):
    result = resolve_missing(diff)
    assert result.source_name == ".env.production"
    assert result.target_name == ".env.staging"


def test_resolve_only_missing_in_target(diff):
    result = resolve_missing(diff)
    keys = [s.key for s in result.suggestions]
    assert "API_KEY" in keys
    assert "LOG_LEVEL" in keys


def test_resolve_excludes_match_and_mismatch_and_missing_in_source(diff):
    result = resolve_missing(diff)
    keys = [s.key for s in result.suggestions]
    assert "DB_HOST" not in keys
    assert "PORT" not in keys
    assert "EXTRA" not in keys


def test_resolve_suggestion_count(diff):
    result = resolve_missing(diff)
    assert result.suggestion_count == 2


def test_resolve_has_suggestions_true(diff):
    assert resolve_missing(diff).has_suggestions is True


def test_resolve_has_suggestions_false_when_no_missing():
    diff = DiffResult(
        source_name="a",
        target_name="b",
        entries=[_entry("X", DiffStatus.MATCH)],
    )
    assert resolve_missing(diff).has_suggestions is False


def test_resolve_copies_source_value_by_default(diff):
    result = resolve_missing(diff)
    api_key_suggestion = next(s for s in result.suggestions if s.key == "API_KEY")
    assert api_key_suggestion.suggested_value == "secret"
    assert api_key_suggestion.reason == "copied from source"


def test_resolve_uses_placeholder_when_provided(diff):
    result = resolve_missing(diff, placeholder="<FILL_ME>")
    for suggestion in result.suggestions:
        assert suggestion.suggested_value == "<FILL_ME>"
        assert suggestion.reason == "placeholder substituted"


def test_resolve_as_dict(diff):
    result = resolve_missing(diff)
    d = result.as_dict()
    assert isinstance(d, dict)
    assert d["API_KEY"] == "secret"
    assert d["LOG_LEVEL"] == "info"


def test_suggestion_source_name_matches_diff_source(diff):
    result = resolve_missing(diff)
    for s in result.suggestions:
        assert s.source_name == ".env.production"
        assert isinstance(s, ResolveSuggestion)
