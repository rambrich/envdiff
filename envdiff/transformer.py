"""Transform .env key/value pairs using rename, prefix, or case operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class TransformOp(str, Enum):
    ADD_PREFIX = "add_prefix"
    REMOVE_PREFIX = "remove_prefix"
    TO_UPPER = "to_upper"
    TO_LOWER = "to_lower"
    SET_VALUE = "set_value"


@dataclass
class TransformRecord:
    key: str
    original_value: Optional[str]
    new_key: str
    new_value: Optional[str]
    op: TransformOp
    changed: bool

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"TransformRecord(key={self.key!r}, new_key={self.new_key!r}, "
            f"op={self.op.value!r}, changed={self.changed})"
        )


@dataclass
class TransformResult:
    env_name: str
    records: List[TransformRecord] = field(default_factory=list)

    @property
    def changed_count(self) -> int:
        return sum(1 for r in self.records if r.changed)

    @property
    def output_env(self) -> Dict[str, Optional[str]]:
        return {r.new_key: r.new_value for r in self.records}


def transform_env(
    env: Dict[str, Optional[str]],
    op: TransformOp,
    *,
    prefix: str = "",
    value: Optional[str] = None,
    keys: Optional[List[str]] = None,
    env_name: str = "env",
) -> TransformResult:
    """Apply *op* to every key in *env* (or only to *keys* if given)."""
    records: List[TransformRecord] = []
    target_keys = set(keys) if keys is not None else set(env.keys())

    for key, val in env.items():
        if key not in target_keys:
            records.append(TransformRecord(key, val, key, val, op, changed=False))
            continue

        if op == TransformOp.ADD_PREFIX:
            new_key = f"{prefix}{key}"
            new_val = val
        elif op == TransformOp.REMOVE_PREFIX:
            new_key = key[len(prefix):] if key.startswith(prefix) else key
            new_val = val
        elif op == TransformOp.TO_UPPER:
            new_key = key.upper()
            new_val = val
        elif op == TransformOp.TO_LOWER:
            new_key = key.lower()
            new_val = val
        elif op == TransformOp.SET_VALUE:
            new_key = key
            new_val = value
        else:  # pragma: no cover
            new_key, new_val = key, val

        changed = new_key != key or new_val != val
        records.append(TransformRecord(key, val, new_key, new_val, op, changed))

    return TransformResult(env_name=env_name, records=records)
