"""Archive and restore .env snapshots to/from a zip archive."""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from envdiff.snapshotter import EnvSnapshot, capture_snapshot


@dataclass
class ArchiveManifest:
    created_at: str
    entries: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"created_at": self.created_at, "entries": self.entries}

    @classmethod
    def from_dict(cls, data: dict) -> "ArchiveManifest":
        return cls(created_at=data["created_at"], entries=data.get("entries", []))


@dataclass
class ArchiveResult:
    path: str
    manifest: ArchiveManifest
    snapshot_count: int


def create_archive(env_paths: List[str], output_path: str) -> ArchiveResult:
    """Capture snapshots of *env_paths* and write them into a zip archive."""
    now = datetime.now(timezone.utc).isoformat()
    manifest = ArchiveManifest(created_at=now)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in env_paths:
            snapshot = capture_snapshot(path)
            entry_name = f"{snapshot.name}.json"
            zf.writestr(entry_name, json.dumps(snapshot.to_dict(), indent=2))
            manifest.entries.append(entry_name)

        zf.writestr("manifest.json", json.dumps(manifest.to_dict(), indent=2))

    return ArchiveResult(
        path=output_path,
        manifest=manifest,
        snapshot_count=len(env_paths),
    )


def load_archive(archive_path: str) -> Dict[str, EnvSnapshot]:
    """Load all snapshots from a zip archive keyed by snapshot name."""
    if not Path(archive_path).exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    snapshots: Dict[str, EnvSnapshot] = {}
    with zipfile.ZipFile(archive_path, "r") as zf:
        for name in zf.namelist():
            if name == "manifest.json":
                continue
            data = json.loads(zf.read(name))
            snap = EnvSnapshot.from_dict(data)
            snapshots[snap.name] = snap
    return snapshots


def read_manifest(archive_path: str) -> ArchiveManifest:
    """Read and return the manifest from an existing zip archive.

    Raises ``FileNotFoundError`` if the archive does not exist and
    ``KeyError`` if the archive contains no manifest entry.
    """
    if not Path(archive_path).exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    with zipfile.ZipFile(archive_path, "r") as zf:
        if "manifest.json" not in zf.namelist():
            raise KeyError(f"No manifest.json found in archive: {archive_path}")
        data = json.loads(zf.read("manifest.json"))
    return ArchiveManifest.from_dict(data)
