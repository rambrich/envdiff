"""CLI entry-point for the env tracker feature."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.parser import parse_env_file
from envdiff.tracker import ChangeType, TrackResult, track_changes

_SYMBOL: dict = {
    ChangeType.ADDED: "+",
    ChangeType.REMOVED: "-",
    ChangeType.MODIFIED: "~",
    ChangeType.UNCHANGED: " ",
}


def _format_result(result: TrackResult, show_unchanged: bool = False) -> str:
    lines: List[str] = [
        f"Tracking changes for: {result.env_name}",
        f"  Added: {result.added_count}  Removed: {result.removed_count}  "
        f"Modified: {result.modified_count}  Unchanged: {result.unchanged_count}",
        "",
    ]
    for change in result.changes:
        if change.change_type == ChangeType.UNCHANGED and not show_unchanged:
            continue
        symbol = _SYMBOL[change.change_type]
        if change.change_type == ChangeType.MODIFIED:
            lines.append(f"  [{symbol}] {change.key}: {change.old_value!r} -> {change.new_value!r}")
        elif change.change_type == ChangeType.ADDED:
            lines.append(f"  [{symbol}] {change.key}: {change.new_value!r}")
        elif change.change_type == ChangeType.REMOVED:
            lines.append(f"  [{symbol}] {change.key}: {change.old_value!r}")
        else:
            lines.append(f"  [{symbol}] {change.key}")
    return "\n".join(lines)


def build_tracker_parser(parent: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    p = parent or argparse.ArgumentParser(
        prog="envdiff-tracker",
        description="Track key changes between two .env file versions.",
    )
    p.add_argument("old", help="Path to the old .env file")
    p.add_argument("new", help="Path to the new .env file")
    p.add_argument("--name", default="env", help="Label for the environment (default: env)")
    p.add_argument("--show-unchanged", action="store_true", help="Include unchanged keys in output")
    p.add_argument("--exit-code", action="store_true", help="Return exit code 1 if changes exist")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_tracker_parser()
    args = parser.parse_args(argv)

    try:
        old_env = parse_env_file(args.old)
        new_env = parse_env_file(args.new)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    result = track_changes(old_env, new_env, env_name=args.name)
    print(_format_result(result, show_unchanged=args.show_unchanged))

    if args.exit_code and result.has_changes:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
