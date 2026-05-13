"""Tests for envdiff.archiver."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from envdiff.archiver import (
    ArchiveManifest,
    ArchiveResult,
    create_archive,
    load_archive,
)


@pytest.fixture()
def env_a(tmp_path: Path) -> str:
    p = tmp_path / "a.env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return str(p)


@pytest.fixture()
def env_b(tmp_path: Path) -> str:
    p = tmp_path / "b.env"
    p.write_text("HELLO=world\n")
    return str(p)


@pytest.fixture()
def archive_path(tmp_path: Path, env_a: str, env_b: str) -> str:
    out = str(tmp_path / "envs.zip")
    create_archive([env_a, env_b], out)
    return out


def test_create_archive_returns_archive_result(tmp_path, env_a, env_b):
    out = str(tmp_path / "out.zip")
    result = create_archive([env_a, env_b], out)
    assert isinstance(result, ArchiveResult)


def test_create_archive_snapshot_count(tmp_path, env_a, env_b):
    out = str(tmp_path / "out.zip")
    result = create_archive([env_a, env_b], out)
    assert result.snapshot_count == 2


def test_create_archive_file_exists(archive_path):
    assert Path(archive_path).exists()


def test_create_archive_is_valid_zip(archive_path):
    assert zipfile.is_zipfile(archive_path)


def test_create_archive_contains_manifest(archive_path):
    with zipfile.ZipFile(archive_path) as zf:
        assert "manifest.json" in zf.namelist()


def test_manifest_has_created_at(archive_path):
    with zipfile.ZipFile(archive_path) as zf:
        manifest = json.loads(zf.read("manifest.json"))
    assert "created_at" in manifest


def test_manifest_entries_count(archive_path):
    with zipfile.ZipFile(archive_path) as zf:
        manifest = json.loads(zf.read("manifest.json"))
    assert len(manifest["entries"]) == 2


def test_load_archive_returns_dict(archive_path):
    snapshots = load_archive(archive_path)
    assert isinstance(snapshots, dict)


def test_load_archive_snapshot_count(archive_path):
    snapshots = load_archive(archive_path)
    assert len(snapshots) == 2


def test_load_archive_snapshot_keys_are_names(archive_path, env_a, env_b):
    snapshots = load_archive(archive_path)
    names = set(snapshots.keys())
    assert len(names) == 2


def test_manifest_round_trip():
    m = ArchiveManifest(created_at="2024-01-01T00:00:00+00:00", entries=["a.json"])
    restored = ArchiveManifest.from_dict(m.to_dict())
    assert restored.created_at == m.created_at
    assert restored.entries == m.entries
