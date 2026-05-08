"""Generate a .env.template file from one or more parsed env dicts.

The template contains all discovered keys with their values replaced by
placeholders, making it easy to share a sanitised skeleton of an env file
with a team.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class TemplateEntry:
    key: str
    placeholder: str
    comment: str = ""

    def __repr__(self) -> str:  # pragma: no cover
        return f"TemplateEntry(key={self.key!r}, placeholder={self.placeholder!r})"


@dataclass
class EnvTemplate:
    entries: list[TemplateEntry] = field(default_factory=list)

    def render(self) -> str:
        """Render the template as a .env-formatted string."""
        lines: list[str] = []
        for entry in self.entries:
            if entry.comment:
                lines.append(f"# {entry.comment}")
            lines.append(f"{entry.key}={entry.placeholder}")
        return "\n".join(lines) + "\n" if lines else ""


def _make_placeholder(key: str) -> str:
    """Return a descriptive placeholder string for *key*."""
    return f"<{key.lower()}>"


def build_template(
    *envs: dict[str, str],
    placeholder_fn: "((str) -> str) | None" = None,
    comments: "dict[str, str] | None" = None,
) -> EnvTemplate:
    """Build an :class:`EnvTemplate` from one or more env dicts.

    Keys are collected from all supplied dicts (union), sorted alphabetically,
    and emitted once each with a generated placeholder.

    Args:
        *envs: One or more ``{key: value}`` dicts produced by
            :func:`envdiff.parser.parse_env_file`.
        placeholder_fn: Optional callable ``(key) -> placeholder_string``.
            Defaults to ``_make_placeholder``.
        comments: Optional ``{key: comment}`` mapping to annotate entries.

    Returns:
        An :class:`EnvTemplate` ready to be rendered.
    """
    if placeholder_fn is None:
        placeholder_fn = _make_placeholder
    if comments is None:
        comments = {}

    all_keys: set[str] = set()
    for env in envs:
        all_keys.update(env.keys())

    entries = [
        TemplateEntry(
            key=key,
            placeholder=placeholder_fn(key),
            comment=comments.get(key, ""),
        )
        for key in sorted(all_keys)
    ]
    return EnvTemplate(entries=entries)


def save_template(template: EnvTemplate, path: str) -> None:
    """Write *template* to *path* on disk."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(template.render())
