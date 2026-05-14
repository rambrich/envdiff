"""Tests for envdiff.pruner and envdiff.cli_pruner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.pruner import PruneRecord, PruneResult, prune_env
from envdiff.cli_pruner import main


# ---------------------------------------------------------------------------
# prune_env unit tests
# ---------------------------------------------------------------------------

def test_prune_returns_prune_result():
    result = prune_env({"A": "1"}, env_name="test")
    assert isinstance(result, PruneResult)


def test_prune_env_name_stored():
    result = prune_env({}, env_name="staging")
    assert result.env_name == "staging"


def test_prune_empty_env_is_clean():
    result = prune_env({})
    assert result.is_clean
    assert result.pruned_count == 0


def test_prune_removes_empty_values():
    result = prune_env({"A": "", "B": "hello"})
    assert result.pruned_count == 1
    assert result.records[0].key == "A"
    assert result.records[0].reason == "empty_value"
    assert "A" not in result.output_env
    assert result.output_env["B"] == "hello"


def test_prune_keep_empty_flag_respected():
    result = prune_env({"A": ""}, remove_empty=False)
    assert result.is_clean
    assert "A" in result.output_env


def test_prune_obsolete_key_flagged():
    result = prune_env({"A": "1", "B": "2"}, reference_keys=["A"])
    assert result.pruned_count == 1
    assert result.records[0].key == "B"
    assert result.records[0].reason == "obsolete_key"
    assert "B" not in result.output_env


def test_prune_no_reference_keeps_all_non_empty():
    env = {"X": "foo", "Y": "bar"}
    result = prune_env(env)
    assert result.is_clean
    assert result.output_env == env


def test_prune_duplicate_values_flagged():
    result = prune_env({"A": "same", "B": "same"}, remove_duplicates=True)
    assert result.pruned_count == 1
    assert result.records[0].key == "B"
    assert "duplicate_value_of_A" in result.records[0].reason


def test_prune_no_dedup_keeps_duplicates():
    result = prune_env({"A": "same", "B": "same"}, remove_duplicates=False)
    assert result.is_clean


def test_prune_record_fields():
    result = prune_env({"EMPTY": ""})
    rec = result.records[0]
    assert isinstance(rec, PruneRecord)
    assert rec.key == "EMPTY"
    assert rec.value == ""


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("A=hello\nB=\nC=world\n")
    return p


def test_main_returns_zero(env_file: Path):
    assert main([str(env_file)]) == 0


def test_main_missing_file_returns_two():
    assert main(["/nonexistent/.env"]) == 2


def test_main_json_output_is_valid(env_file: Path, capsys):
    main([str(env_file), "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "pruned_count" in data
    assert "records" in data


def test_main_json_flags_empty_key(env_file: Path, capsys):
    main([str(env_file), "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    keys_pruned = [r["key"] for r in data["records"]]
    assert "B" in keys_pruned


def test_main_with_reference(tmp_path: Path):
    src = tmp_path / "src.env"
    ref = tmp_path / "ref.env"
    src.write_text("A=1\nOBSOLETE=yes\n")
    ref.write_text("A=1\n")
    assert main([str(src), "--reference", str(ref)]) == 0


def test_main_missing_reference_returns_two(env_file: Path):
    assert main([str(env_file), "--reference", "/no/such/ref.env"]) == 2
