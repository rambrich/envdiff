"""Tests for envdiff.pinner and envdiff.cli_pinner."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from envdiff.pinner import PinViolation, PinResult, check_pins
from envdiff.cli_pinner import main


# ---------------------------------------------------------------------------
# Unit tests – check_pins
# ---------------------------------------------------------------------------

def test_check_pins_returns_pin_result():
    result = check_pins({"APP_ENV": "production"}, {"APP_ENV": "production"})
    assert isinstance(result, PinResult)


def test_check_pins_no_violations_when_all_match():
    env = {"APP_ENV": "production", "DEBUG": "false"}
    result = check_pins(env, {"APP_ENV": "production", "DEBUG": "false"})
    assert result.is_pinned is True
    assert result.violation_count == 0


def test_check_pins_violation_on_value_mismatch():
    env = {"APP_ENV": "staging"}
    result = check_pins(env, {"APP_ENV": "production"})
    assert result.is_pinned is False
    assert result.violation_count == 1
    assert result.violations[0].key == "APP_ENV"
    assert result.violations[0].pinned_value == "production"
    assert result.violations[0].actual_value == "staging"


def test_check_pins_violation_on_missing_key():
    result = check_pins({}, {"APP_ENV": "production"})
    assert result.violation_count == 1
    assert result.violations[0].actual_value is None


def test_check_pins_env_name_stored():
    result = check_pins({}, {}, env_name=".env.prod")
    assert result.env_name == ".env.prod"


def test_check_pins_keys_with_violations():
    env = {"A": "wrong", "B": "ok"}
    result = check_pins(env, {"A": "right", "B": "ok"})
    assert result.keys_with_violations() == ["A"]


def test_pin_violation_fields():
    v = PinViolation(key="X", pinned_value="1", actual_value="2", env_name="e")
    assert v.key == "X"
    assert v.pinned_value == "1"
    assert v.actual_value == "2"


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent("""\
        APP_ENV=production
        DEBUG=false
    """))
    return p


def test_main_returns_zero_all_match(env_file):
    assert main([str(env_file), "APP_ENV=production", "DEBUG=false"]) == 0


def test_main_returns_zero_with_violations_no_exit_code_flag(env_file):
    assert main([str(env_file), "APP_ENV=staging"]) == 0


def test_main_returns_one_with_violations_and_exit_code_flag(env_file):
    assert main([str(env_file), "APP_ENV=staging", "--exit-code"]) == 1


def test_main_returns_two_for_missing_file(tmp_path):
    assert main([str(tmp_path / "missing.env"), "KEY=val"]) == 2


def test_main_returns_two_for_invalid_pin(env_file):
    assert main([str(env_file), "NOEQUALS"]) == 2


def test_main_json_output_is_valid_json(env_file, capsys):
    main([str(env_file), "APP_ENV=production", "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "violations" in data
    assert "is_pinned" in data


def test_main_json_contains_violation_detail(env_file, capsys):
    main([str(env_file), "APP_ENV=staging", "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert data["violation_count"] == 1
    assert data["violations"][0]["key"] == "APP_ENV"
