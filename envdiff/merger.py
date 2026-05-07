"""Merge multiple .env files into a unified view, resolving conflicts by strategy."""

from enum import Enum
from typing import Dict, List, Optional

from envdiff.differ import DiffEntry, DiffStatus


class MergeStrategy(str, Enum):
    FIRST = "first"   # Keep value from the first file that defines the key
    LAST = "last"     # Keep value from the last file that defines the key
    STRICT = "strict" # Raise if any key has conflicting values


class MergeConflict(Exception):
    """Raised when STRICT strategy encounters conflicting values."""

    def __init__(self, key: str, values: Dict[str, Optional[str]]):
        self.key = key
        self.values = values
        super().__init__(
            f"Conflict for key '{key}': {values}"
        )


def merge_envs(
    envs: Dict[str, Dict[str, Optional[str]]],
    strategy: MergeStrategy = MergeStrategy.FIRST,
) -> Dict[str, Optional[str]]:
    """Merge multiple env dicts into one according to the given strategy.

    Args:
        envs: Mapping of env-name -> key/value dict.
        strategy: How to resolve conflicting values for the same key.

    Returns:
        A single merged dict of key -> value.
    """
    merged: Dict[str, Optional[str]] = {}
    sources: Dict[str, str] = {}  # key -> env name that last set it

    for env_name, env_vars in envs.items():
        for key, value in env_vars.items():
            if key not in merged:
                merged[key] = value
                sources[key] = env_name
            else:
                existing = merged[key]
                if existing == value:
                    continue  # identical — no conflict
                if strategy == MergeStrategy.STRICT:
                    raise MergeConflict(key, {sources[key]: existing, env_name: value})
                elif strategy == MergeStrategy.LAST:
                    merged[key] = value
                    sources[key] = env_name
                # FIRST: do nothing, keep existing

    return merged


def merge_to_entries(
    envs: Dict[str, Dict[str, Optional[str]]],
    strategy: MergeStrategy = MergeStrategy.FIRST,
) -> List[DiffEntry]:
    """Merge envs and return DiffEntry list marking each key's status.

    Keys present in all envs with the same value -> MATCH.
    Keys missing from at least one env -> MISSING_IN_TARGET.
    Keys with differing values (non-strict) -> MISMATCH.
    """
    all_keys = {k for env in envs.values() for k in env}
    env_names = list(envs.keys())
    entries: List[DiffEntry] = []

    for key in sorted(all_keys):
        values = {name: envs[name].get(key) for name in env_names}
        present = [v for v in values.values() if v is not None]
        missing_in = [n for n in env_names if key not in envs[n]]

        if missing_in:
            status = DiffStatus.MISSING_IN_TARGET
        elif len(set(present)) > 1:
            status = DiffStatus.MISMATCH
        else:
            status = DiffStatus.MATCH

        merged_value = merge_envs(envs, strategy).get(key)
        source_value = envs[env_names[0]].get(key) if env_names else None
        target_value = envs[env_names[-1]].get(key) if len(env_names) > 1 else merged_value

        entries.append(DiffEntry(key=key, status=status, source_value=source_value, target_value=target_value))

    return entries
