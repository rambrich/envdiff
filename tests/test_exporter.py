"""Tests for envdiff.exporter."""

from __future__ import annotations

import csv
import io
import json

import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.exporter import export_diff_result, export_to_csv, export_to_json


@pytest.fixture()
def result() -> DiffResult:
    return DiffResult(
        source_name=".env.production",
        target_name=".env.staging",
        entries=[
            DiffEntry(key="DATABASE_URL", status=DiffStatus.MATCH, source_value="db://prod", target_value="db://prod"),
            DiffEntry(key="SECRET_KEY", status=DiffStatus.MISSING_IN_TARGET, source_value="abc123", target_value=None),
            DiffEntry(key="DEBUG", status=DiffStatus.MISSING_IN_SOURCE, source_value=None, target_value="true"),
            DiffEntry(key="API_URL", status=DiffStatus.MISMATCH, source_value="https://prod", target_value="https://staging"),
        ],
    )


# --- JSON ---

def test_export_json_is_valid_json(result):
    output = export_to_json(result)
    parsed = json.loads(output)
    assert isinstance(parsed, dict)


def test_export_json_contains_source_and_target(result):
    parsed = json.loads(export_to_json(result))
    assert parsed["source"] == ".env.production"
    assert parsed["target"] == ".env.staging"


def test_export_json_entry_count(result):
    parsed = json.loads(export_to_json(result))
    assert len(parsed["entries"]) == 4


def test_export_json_entry_fields(result):
    parsed = json.loads(export_to_json(result))
    entry = next(e for e in parsed["entries"] if e["key"] == "API_URL")
    assert entry["status"] == "mismatch"
    assert entry["source_value"] == "https://prod"
    assert entry["target_value"] == "https://staging"


def test_export_json_null_values(result):
    parsed = json.loads(export_to_json(result))
    missing = next(e for e in parsed["entries"] if e["key"] == "SECRET_KEY")
    assert missing["target_value"] is None


# --- CSV ---

def test_export_csv_has_header(result):
    output = export_to_csv(result)
    reader = csv.DictReader(io.StringIO(output))
    assert reader.fieldnames == ["key", "status", "source_value", "target_value"]


def test_export_csv_row_count(result):
    output = export_to_csv(result)
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 4


def test_export_csv_empty_string_for_none(result):
    output = export_to_csv(result)
    reader = csv.DictReader(io.StringIO(output))
    rows = {r["key"]: r for r in reader}
    assert rows["SECRET_KEY"]["target_value"] == ""
    assert rows["DEBUG"]["source_value"] == ""


# --- dispatch ---

def test_export_diff_result_json(result):
    output = export_diff_result(result, "json")
    assert json.loads(output)["source"] == ".env.production"


def test_export_diff_result_csv(result):
    output = export_diff_result(result, "csv")
    assert "key,status" in output


def test_export_diff_result_invalid_format(result):
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_diff_result(result, "xml")  # type: ignore[arg-type]
