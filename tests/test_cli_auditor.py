"""Tests for envdiff.cli_auditor."""
from __future__ import annotations

import json
import textwrap

import pytest

from envdiff.cli_auditor import main


@pytest.fixture()
def env_source(tmp_path):
    p = tmp_path / "source.env"
    p.write_text(textwrap.dedent("""\
        SHARED=same
        ONLY_IN_SOURCE=yes
        MISMATCH=old
    """))
    return str(p)


@pytest.fixture()
def env_target(tmp_path):
    p = tmp_path / "target.env"
    p.write_text(textwrap.dedent("""\
        SHARED=same
        ONLY_IN_TARGET=yes
        MISMATCH=new
    """))
    return str(p)


def test_main_returns_zero(env_source, env_target):
    assert main([env_source, env_target]) == 0


def test_main_missing_source_returns_two(env_target, tmp_path):
    assert main([str(tmp_path / "nope.env"), env_target]) == 2


def test_main_missing_target_returns_two(env_source, tmp_path):
    assert main([env_source, str(tmp_path / "nope.env")]) == 2


def test_main_json_output_is_valid_json(env_source, env_target, capsys):
    main([env_source, env_target, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "entries" in data


def test_main_json_entry_count(env_source, env_target, capsys):
    main([env_source, env_target, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    # 3 keys total across both files (SHARED match, ONLY_IN_SOURCE, ONLY_IN_TARGET, MISMATCH)
    assert data["entry_count"] == 4


def test_main_json_contains_operations(env_source, env_target, capsys):
    main([env_source, env_target, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    ops = {e["operation"] for e in data["entries"]}
    assert "match" in ops
    assert "value_mismatch" in ops


def test_main_text_output_contains_key(env_source, env_target, capsys):
    main([env_source, env_target])
    out = capsys.readouterr().out
    assert "MISMATCH" in out


def test_main_custom_name_in_json(env_source, env_target, capsys):
    main([env_source, env_target, "--name", "prod-audit", "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["env_name"] == "prod-audit"
