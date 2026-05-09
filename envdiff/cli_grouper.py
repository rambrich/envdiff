"""CLI interface for the grouper module."""

from __future__ import annotations

import argparse
import sys

from envdiff.differ import diff_envs
from envdiff.grouper import GroupedResult, group_by_prefix
from envdiff.parser import parse_env_file


def _format_result(grouped: GroupedResult) -> str:
    lines: list[str] = [
        f"Grouped diff: {grouped.source} vs {grouped.target}",
        "",
    ]
    for name in grouped.group_names:
        group = grouped.groups[name]
        lines.append(f"[{name}]  ({group.count} key(s))")
        for entry in sorted(group.entries, key=lambda e: e.key):
            lines.append(f"  {entry.key:<30} {entry.status.value}")
        lines.append("")
    return "\n".join(lines).rstrip()


def build_grouper_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    description = "Group diff entries by key prefix."
    if parent is not None:
        parser = parent.add_parser("group", help=description)
    else:
        parser = argparse.ArgumentParser(
            prog="envdiff-group",
            description=description,
        )
    parser.add_argument("source", help="Source .env file")
    parser.add_argument("target", help="Target .env file")
    parser.add_argument(
        "--separator",
        default="_",
        help="Key prefix separator (default: '_')",
    )
    parser.add_argument(
        "--ungrouped-label",
        default="OTHER",
        dest="ungrouped_label",
        help="Label for keys without a prefix (default: OTHER)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_grouper_parser()
    args = parser.parse_args(argv)

    try:
        src_env = parse_env_file(args.source)
        tgt_env = parse_env_file(args.target)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    result = diff_envs(src_env, tgt_env, source=args.source, target=args.target)
    grouped = group_by_prefix(
        result,
        separator=args.separator,
        ungrouped_label=args.ungrouped_label,
    )
    print(_format_result(grouped))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
