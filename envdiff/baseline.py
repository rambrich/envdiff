"""Baseline management for .env files — save and compare against a known-good state."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Optional

from envdiff.differ import DiffResult, diff


@dataclass
class Baseline:
    """A saved snapshot of an environment's key-value pairs."""

    name: str
    env: Dict[str, str] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Baseline":
        return cls(
            name=data["name"],
            env=data.get("env", {}),
            description=data.get("description", ""),
        )


def save_baseline(baseline: Baseline, path: Path) -> None:
    """Persist a baseline to a JSON file."""
    path.write_text(json.dumps(baseline.to_dict(), indent=2), encoding="utf-8")


def load_baseline(path: Path) -> Baseline:
    """Load a baseline from a JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return Baseline.from_dict(data)


def compare_to_baseline(
    baseline: Baseline,
    current_env: Dict[str, str],
    current_name: Optional[str] = None,
) -> DiffResult:
    """Diff a current env dict against a saved baseline."""
    target_name = current_name or "current"
    return diff(baseline.env, current_env, source_name=baseline.name, target_name=target_name)
