"""Tests for envdiff.cli_transform."""
import json
import pytest

from envdiff.cli_transform import main


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_HOST=localhost\nAPP_PORT=8080\nDEBUG=true\n")
    return str(p)


# --- exit codes ---

def test_main_returns_zero_on_success(env_file):
    assert main([env_file, "to_upper"]) == 0


def test_main_returns_two_for_missing_file():
    assert main(["nonexistent.env", "to_upper"]) == 2


# --- text output ---

def test_text_output_add_prefix(env_file, capsys):
    main([env_file, "add_prefix", "--prefix", "X_"])
    out = capsys.readouterr().out
    assert "X_APP_HOST=localhost" in out
    assert "X_DEBUG=true" in out


def test_text_output_remove_prefix(env_file, capsys):
    main([env_file, "remove_prefix", "--prefix", "APP_"])
    out = capsys.readouterr().out
    assert "HOST=localhost" in out
    assert "PORT=8080" in out


def test_text_output_to_lower(env_file, capsys):
    main([env_file, "to_lower"])
    out = capsys.readouterr().out
    assert "app_host=localhost" in out
    assert "debug=true" in out


def test_text_output_set_value(env_file, capsys):
    main([env_file, "set_value", "--value", "***"])
    out = capsys.readouterr().out
    assert "APP_HOST=***" in out
    assert "DEBUG=***" in out


# --- json output ---

def test_json_output_is_valid_json(env_file, capsys):
    main([env_file, "add_prefix", "--prefix", "P_", "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, dict)


def test_json_output_contains_changed_count(env_file, capsys):
    main([env_file, "add_prefix", "--prefix", "P_", "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert data["changed_count"] == 3


def test_json_output_contains_output_env(env_file, capsys):
    main([env_file, "add_prefix", "--prefix", "P_", "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert "P_APP_HOST" in data["output"]


def test_json_output_env_name_override(env_file, capsys):
    main([env_file, "to_upper", "--name", "prod", "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert data["env_name"] == "prod"


# --- keys filter ---

def test_keys_filter_only_changes_specified_key(env_file, capsys):
    main([env_file, "add_prefix", "--prefix", "Z_", "--keys", "DEBUG"])
    out = capsys.readouterr().out
    assert "Z_DEBUG=true" in out
    # Other keys should remain unchanged
    assert "APP_HOST=localhost" in out
