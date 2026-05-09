"""Detect and resolve variable interpolation references in .env files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_REF_PATTERN = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolationRef:
    """A single variable reference found inside a value."""

    key: str          # the key whose value contains the reference
    ref_name: str     # the referenced variable name
    resolved: Optional[str] = None   # resolved value, or None if unresolvable

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"InterpolationRef(key={self.key!r}, ref_name={self.ref_name!r}, "
            f"resolved={self.resolved!r})"
        )


@dataclass
class InterpolationResult:
    """Result of analysing an env dict for interpolation references."""

    env_name: str
    refs: List[InterpolationRef] = field(default_factory=list)
    resolved_env: Dict[str, str] = field(default_factory=dict)

    @property
    def unresolved_count(self) -> int:
        return sum(1 for r in self.refs if r.resolved is None)

    @property
    def has_unresolved(self) -> bool:
        return self.unresolved_count > 0

    @property
    def ref_count(self) -> int:
        return len(self.refs)


def _find_refs(key: str, value: str) -> List[str]:
    """Return all variable names referenced inside *value*."""
    names: List[str] = []
    for m in _REF_PATTERN.finditer(value):
        names.append(m.group(1) or m.group(2))
    return names


def interpolate_env(
    env: Dict[str, str],
    env_name: str = "env",
) -> InterpolationResult:
    """Analyse *env* for variable references and attempt to resolve them.

    Resolution is single-pass: a reference is resolved only when the
    referenced key already exists in *env* (possibly with its own literal
    value).  Circular or forward references that cannot be resolved in one
    pass are left as ``None``.
    """
    refs: List[InterpolationRef] = []
    resolved_env: Dict[str, str] = {}

    for key, value in env.items():
        ref_names = _find_refs(key, value)
        if ref_names:
            for ref_name in ref_names:
                resolved_value = env.get(ref_name)  # None if missing
                refs.append(InterpolationRef(key=key, ref_name=ref_name, resolved=resolved_value))

        # Build a best-effort resolved copy of the env
        def _replace(m: re.Match) -> str:  # noqa: E306
            name = m.group(1) or m.group(2)
            return env.get(name, m.group(0))

        resolved_env[key] = _REF_PATTERN.sub(_replace, value)

    return InterpolationResult(env_name=env_name, refs=refs, resolved_env=resolved_env)
