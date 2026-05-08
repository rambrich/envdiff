"""Tests for envdiff.templater."""
from __future__ import annotations

import os
import pytest

from envdiff.templater import (
    EnvTemplate,
    TemplateEntry,
    build_template,
    save_template,
    _make_placeholder,
)


# ---------------------------------------------------------------------------
# _make_placeholder
# ---------------------------------------------------------------------------

def test_make_placeholder_lowercases_key():
    assert _make_placeholder("DB_HOST") == "<db_host>"


def test_make_placeholder_wraps_in_angle_brackets():
    result = _make_placeholder("SECRET")
    assert result.startswith("<") and result.endswith(">")


# ---------------------------------------------------------------------------
# build_template
# ---------------------------------------------------------------------------

def test_build_template_returns_env_template():
    result = build_template({"A": "1"})
    assert isinstance(result, EnvTemplate)


def test_build_template_single_env_keys():
    result = build_template({"Z": "z", "A": "a"})
    keys = [e.key for e in result.entries]
    assert keys == ["A", "Z"]


def test_build_template_keys_sorted_alphabetically():
    env = {"GAMMA": "g", "ALPHA": "a", "BETA": "b"}
    result = build_template(env)
    assert [e.key for e in result.entries] == ["ALPHA", "BETA", "GAMMA"]


def test_build_template_merges_multiple_envs():
    env1 = {"A": "1", "B": "2"}
    env2 = {"B": "2", "C": "3"}
    result = build_template(env1, env2)
    assert {e.key for e in result.entries} == {"A", "B", "C"}


def test_build_template_no_duplicate_keys():
    result = build_template({"X": "1"}, {"X": "2"})
    assert len(result.entries) == 1


def test_build_template_placeholder_uses_key():
    result = build_template({"API_KEY": "secret"})
    assert result.entries[0].placeholder == "<api_key>"


def test_build_template_custom_placeholder_fn():
    result = build_template({"FOO": "bar"}, placeholder_fn=lambda k: f"${{{k}}}")
    assert result.entries[0].placeholder == "${FOO}"


def test_build_template_comments_attached():
    result = build_template({"PORT": "8080"}, comments={"PORT": "HTTP port"})
    assert result.entries[0].comment == "HTTP port"


def test_build_template_empty_env():
    result = build_template({})
    assert result.entries == []


# ---------------------------------------------------------------------------
# EnvTemplate.render
# ---------------------------------------------------------------------------

def test_render_empty_template():
    t = EnvTemplate(entries=[])
    assert t.render() == ""


def test_render_produces_key_equals_placeholder():
    t = EnvTemplate(entries=[TemplateEntry(key="HOST", placeholder="<host>")])
    assert "HOST=<host>" in t.render()


def test_render_includes_comment_line():
    t = EnvTemplate(
        entries=[TemplateEntry(key="DB", placeholder="<db>", comment="database url")]
    )
    rendered = t.render()
    assert "# database url" in rendered
    assert rendered.index("# database url") < rendered.index("DB=<db>")


def test_render_ends_with_newline():
    t = EnvTemplate(entries=[TemplateEntry(key="K", placeholder="<k>")])
    assert t.render().endswith("\n")


# ---------------------------------------------------------------------------
# save_template
# ---------------------------------------------------------------------------

def test_save_template_creates_file(tmp_path):
    path = str(tmp_path / ".env.template")
    t = build_template({"FOO": "bar"})
    save_template(t, path)
    assert os.path.exists(path)


def test_save_template_file_content(tmp_path):
    path = str(tmp_path / ".env.template")
    t = build_template({"FOO": "bar"})
    save_template(t, path)
    content = open(path).read()
    assert "FOO=<foo>" in content
