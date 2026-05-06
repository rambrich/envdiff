"""Tests for envdiff.validator module."""

import pytest

from envdiff.validator import (
    ValidationRule,
    ValidationViolation,
    ValidationResult,
    validate_env,
)


@pytest.fixture
def sample_env() -> dict:
    return {
        "DATABASE_URL": "postgres://localhost/mydb",
        "PORT": "8080",
        "DEBUG": "true",
    }


@pytest.fixture
def basic_rules() -> list:
    return [
        ValidationRule(key="DATABASE_URL", required=True),
        ValidationRule(key="PORT", pattern=r"\d+", required=True),
        ValidationRule(key="DEBUG", pattern=r"true|false", required=False),
    ]


# --- ValidationResult ---

def test_validation_result_is_valid_when_no_violations():
    result = ValidationResult(env_name="test")
    assert result.is_valid is True


def test_validation_result_is_invalid_when_violations_exist():
    result = ValidationResult(env_name="test")
    result.add_violation(key="FOO", message="missing")
    assert result.is_valid is False


def test_validation_result_stores_env_name():
    result = ValidationResult(env_name="production")
    assert result.env_name == "production"


def test_add_violation_appends_entry():
    result = ValidationResult(env_name="test")
    result.add_violation(key="KEY", message="bad value", value="x")
    assert len(result.violations) == 1
    v = result.violations[0]
    assert isinstance(v, ValidationViolation)
    assert v.key == "KEY"
    assert v.value == "x"


# --- validate_env ---

def test_validate_passes_with_valid_env(sample_env, basic_rules):
    result = validate_env(sample_env, basic_rules, env_name="staging")
    assert result.is_valid
    assert result.violations == []


def test_validate_reports_missing_required_key(basic_rules):
    env = {"PORT": "3000", "DEBUG": "false"}  # DATABASE_URL missing
    result = validate_env(env, basic_rules)
    assert not result.is_valid
    keys = [v.key for v in result.violations]
    assert "DATABASE_URL" in keys


def test_validate_does_not_report_missing_optional_key():
    rules = [ValidationRule(key="OPTIONAL_KEY", required=False)]
    result = validate_env({}, rules)
    assert result.is_valid


def test_validate_reports_pattern_mismatch(basic_rules):
    env = {
        "DATABASE_URL": "postgres://localhost/mydb",
        "PORT": "not-a-number",
        "DEBUG": "true",
    }
    result = validate_env(env, basic_rules)
    assert not result.is_valid
    assert any(v.key == "PORT" for v in result.violations)


def test_validate_violation_includes_bad_value(basic_rules):
    env = {"DATABASE_URL": "postgres://x", "PORT": "abc", "DEBUG": "true"}
    result = validate_env(env, basic_rules)
    port_violation = next(v for v in result.violations if v.key == "PORT")
    assert port_violation.value == "abc"


def test_validate_multiple_violations(basic_rules):
    env = {"PORT": "bad", "DEBUG": "yes"}  # missing DATABASE_URL, bad PORT, bad DEBUG
    result = validate_env(env, basic_rules)
    assert len(result.violations) == 3


def test_validate_env_name_stored_in_result(sample_env, basic_rules):
    result = validate_env(sample_env, basic_rules, env_name="production")
    assert result.env_name == "production"


def test_validate_empty_rules(sample_env):
    result = validate_env(sample_env, [])
    assert result.is_valid
