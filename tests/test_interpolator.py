"""Tests for envdiff.interpolator."""
import pytest
from envdiff.interpolator import (
    InterpolationRef,
    InterpolationResult,
    interpolate_env,
)


@pytest.fixture()
def simple_env() -> dict:
    return {
        "HOST": "localhost",
        "PORT": "5432",
        "DB_URL": "postgres://${HOST}:${PORT}/mydb",
        "ALIAS": "$HOST",
    }


def test_interpolate_returns_interpolation_result(simple_env):
    result = interpolate_env(simple_env)
    assert isinstance(result, InterpolationResult)


def test_interpolate_env_name_stored(simple_env):
    result = interpolate_env(simple_env, env_name="production")
    assert result.env_name == "production"


def test_interpolate_ref_count(simple_env):
    result = interpolate_env(simple_env)
    # DB_URL references HOST and PORT; ALIAS references HOST → 3 refs total
    assert result.ref_count == 3


def test_interpolate_refs_are_interpolation_ref_instances(simple_env):
    result = interpolate_env(simple_env)
    for ref in result.refs:
        assert isinstance(ref, InterpolationRef)


def test_interpolate_resolved_values_for_known_refs(simple_env):
    result = interpolate_env(simple_env)
    host_ref = next(r for r in result.refs if r.ref_name == "HOST" and r.key == "ALIAS")
    assert host_ref.resolved == "localhost"


def test_interpolate_unresolved_ref_is_none():
    env = {"FOO": "${MISSING_VAR}"}
    result = interpolate_env(env)
    assert result.refs[0].resolved is None


def test_interpolate_has_unresolved_true_when_missing():
    env = {"FOO": "${MISSING_VAR}"}
    result = interpolate_env(env)
    assert result.has_unresolved is True


def test_interpolate_has_unresolved_false_when_all_resolve(simple_env):
    result = interpolate_env(simple_env)
    assert result.has_unresolved is False


def test_interpolate_unresolved_count(simple_env):
    result = interpolate_env(simple_env)
    assert result.unresolved_count == 0


def test_interpolate_resolved_env_replaces_references(simple_env):
    result = interpolate_env(simple_env)
    assert result.resolved_env["DB_URL"] == "postgres://localhost:5432/mydb"


def test_interpolate_resolved_env_dollar_syntax():
    env = {"BASE": "http", "URL": "$BASE://example.com"}
    result = interpolate_env(env)
    assert result.resolved_env["URL"] == "http://example.com"


def test_interpolate_literal_values_unchanged(simple_env):
    result = interpolate_env(simple_env)
    assert result.resolved_env["HOST"] == "localhost"
    assert result.resolved_env["PORT"] == "5432"


def test_interpolate_empty_env():
    result = interpolate_env({})
    assert result.ref_count == 0
    assert result.has_unresolved is False
    assert result.resolved_env == {}
