"""CLI for the tagger module."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.parser import parse_env_file
from envdiff.tagger import TagRule, TagResult, tag_env


def _parse_rules(raw: List[str]) -> List[TagRule]:
    """Convert ``TAG:PATTERN`` strings into :class:`TagRule` objects."""
    rules: List[TagRule] = []
    for item in raw:
        if ":" not in item:
            raise ValueError(
                f"Invalid rule {item!r}: expected format TAG:PATTERN"
            )
        tag, _, pattern = item.partition(":")
        rules.append(TagRule(tag=tag.strip(), pattern=pattern.strip()))
    return rules


def _format_result(result: TagResult, fmt: str) -> str:
    if fmt == "json":
        data = {
            "env_name": result.env_name,
            "all_tags": result.all_tags,
            "entries": [
                {"key": e.key, "tags": e.tags} for e in result.entries
            ],
        }
        return json.dumps(data, indent=2)

    # text
    lines = [f"Tagging report for: {result.env_name}"]
    lines.append("-" * 40)
    for entry in result.entries:
        tag_str = ", ".join(entry.tags) if entry.tags else "(untagged)"
        lines.append(f"  {entry.key:<30} [{tag_str}]")
    lines.append("")
    lines.append(f"Tags found: {', '.join(result.all_tags) or 'none'}")
    return "\n".join(lines)


def build_tagger_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-tag",
        description="Tag .env keys using pattern-based rules.",
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument(
        "--rule",
        dest="rules",
        metavar="TAG:PATTERN",
        action="append",
        default=[],
        help="Rule in TAG:PATTERN format (repeatable)",
    )
    p.add_argument(
        "--untagged-label",
        default=None,
        metavar="LABEL",
        help="Tag to assign keys that match no rule",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return p


def main(argv: List[str] | None = None) -> int:
    parser = build_tagger_parser()
    args = parser.parse_args(argv)

    try:
        env = parse_env_file(args.env_file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.env_file}", file=sys.stderr)
        return 2

    try:
        rules = _parse_rules(args.rules)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    result = tag_env(
        env,
        rules,
        env_name=args.env_file,
        untagged_label=args.untagged_label,
    )
    print(_format_result(result, args.format))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
