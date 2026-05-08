"""Profile .env files to produce statistics and insights about their contents."""

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class EnvProfile:
    """Statistical profile of a single .env environment."""

    env_name: str
    total_keys: int
    empty_value_keys: List[str] = field(default_factory=list)
    numeric_value_keys: List[str] = field(default_factory=list)
    boolean_value_keys: List[str] = field(default_factory=list)
    url_value_keys: List[str] = field(default_factory=list)

    @property
    def empty_count(self) -> int:
        return len(self.empty_value_keys)

    @property
    def numeric_count(self) -> int:
        return len(self.numeric_value_keys)

    @property
    def boolean_count(self) -> int:
        return len(self.boolean_value_keys)

    @property
    def url_count(self) -> int:
        return len(self.url_value_keys)


@dataclass
class DiffProfile:
    """Combined profile derived from a DiffResult."""

    source_profile: EnvProfile
    target_profile: EnvProfile
    overlap_count: int
    unique_to_source: int
    unique_to_target: int


def _is_numeric(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _is_boolean(value: str) -> bool:
    return value.lower() in {"true", "false", "yes", "no", "1", "0"}


def _is_url(value: str) -> bool:
    return value.startswith(("http://", "https://", "ftp://"))


def profile_env(env: Dict[str, str], env_name: str = "env") -> EnvProfile:
    """Build a profile from a parsed env dictionary."""
    empty_keys: List[str] = []
    numeric_keys: List[str] = []
    boolean_keys: List[str] = []
    url_keys: List[str] = []

    for key, value in env.items():
        if value == "":
            empty_keys.append(key)
        elif _is_boolean(value):
            boolean_keys.append(key)
        elif _is_numeric(value):
            numeric_keys.append(key)
        elif _is_url(value):
            url_keys.append(key)

    return EnvProfile(
        env_name=env_name,
        total_keys=len(env),
        empty_value_keys=sorted(empty_keys),
        numeric_value_keys=sorted(numeric_keys),
        boolean_value_keys=sorted(boolean_keys),
        url_value_keys=sorted(url_keys),
    )


def profile_diff(result: DiffResult) -> DiffProfile:
    """Derive a DiffProfile from a DiffResult."""
    source_env: Dict[str, str] = {}
    target_env: Dict[str, str] = {}
    overlap = 0
    unique_source = 0
    unique_target = 0

    for entry in result.entries:
        if entry.status == DiffStatus.MATCH or entry.status == DiffStatus.MISMATCH:
            if entry.source_value is not None:
                source_env[entry.key] = entry.source_value
            if entry.target_value is not None:
                target_env[entry.key] = entry.target_value
            overlap += 1
        elif entry.status == DiffStatus.MISSING_IN_TARGET:
            if entry.source_value is not None:
                source_env[entry.key] = entry.source_value
            unique_source += 1
        elif entry.status == DiffStatus.MISSING_IN_SOURCE:
            if entry.target_value is not None:
                target_env[entry.key] = entry.target_value
            unique_target += 1

    return DiffProfile(
        source_profile=profile_env(source_env, env_name=result.source_name),
        target_profile=profile_env(target_env, env_name=result.target_name),
        overlap_count=overlap,
        unique_to_source=unique_source,
        unique_to_target=unique_target,
    )
