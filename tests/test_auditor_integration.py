"""Integration tests for auditor — round-trip from file to audit log."""
from __future__ import annotations

import textwrap

import pytest

from envdiff.auditor import audit_diff_result
from envdiff.differ import diff_envs
from envdiff.parser import parse_env_file


@pytest.fixture()
def env_a(tmp_path):
    p = tmp_path / "a.env"
    p.write_text(textwrap.dedent("""\
        DB_HOST=localhost
        DB_PORT=5432
        SECRET=abc123
    """))
    return p


@pytest.fixture()
def env_b(tmp_path):
    p = tmp_path / "b.env"
    p.write_text(textwrap.dedent("""\
        DB_HOST=prod.example.com
        DB_PORT=5432
        NEW_KEY=hello
    """))
    return p


def test_integration_audit_entry_count(env_a, env_b):
    src = parse_env_file(str(env_a))
    tgt = parse_env_file(str(env_b))
    result = diff_envs(src, tgt, source_name="a", target_name="b")
    log = audit_diff_result(result, env_name="integration")
    # DB_HOST mismatch, DB_PORT match, SECRET missing_in_target, NEW_KEY missing_in_source
    assert log.entry_count == 4


def test_integration_audit_detects_mismatch(env_a, env_b):
    src = parse_env_file(str(env_a))
    tgt = parse_env_file(str(env_b))
    result = diff_envs(src, tgt, source_name="a", target_name="b")
    log = audit_diff_result(result)
    mismatches = log.for_operation("value_mismatch")
    assert any(e.key == "DB_HOST" for e in mismatches)


def test_integration_audit_detects_missing_in_target(env_a, env_b):
    src = parse_env_file(str(env_a))
    tgt = parse_env_file(str(env_b))
    result = diff_envs(src, tgt, source_name="a", target_name="b")
    log = audit_diff_result(result)
    missing = log.for_operation("missing_in_target")
    assert any(e.key == "SECRET" for e in missing)


def test_integration_audit_detects_missing_in_source(env_a, env_b):
    src = parse_env_file(str(env_a))
    tgt = parse_env_file(str(env_b))
    result = diff_envs(src, tgt, source_name="a", target_name="b")
    log = audit_diff_result(result)
    missing = log.for_operation("missing_in_source")
    assert any(e.key == "NEW_KEY" for e in missing)
