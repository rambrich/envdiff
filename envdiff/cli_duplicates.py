"""CLI entry-point for the duplicate-key detector."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.duplicates import DuplicateResult, find_duplicates


def _format_result(result: DuplicateResult) -> str:
    lines: list[str] = []
    lines.append(f"Duplicate-key report for: {result.env_name}")
    lines.append("-" * 40)

    if not result.has_duplicates:
        lines.append("No duplicate keys found. ✓")
        return "\n".join(lines)

    lines.append(
        f"Found {result.duplicate_count} duplicate key(s):\n"
    )
    for dup in sorted(result.duplicates, key=lambda d: d.key):
        lines.append(f"  {dup.key}  ({dup.count} occurrences)")
        for lineno, value in zip(dup.line_numbers, dup.values):
            lines.append(f"    line {lineno}: {value!r}")

    return "\n".join(lines)


def build_duplicates_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-duplicates",
        description="Detect duplicate keys in a .env file.",
    )
    parser.add_argument("env_file", help="Path to the .env file to inspect.")
    parser.add_argument(
        "--name",
        default=None,
        metavar="NAME",
        help="Override the display name for the environment.",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when duplicates are found.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_duplicates_parser()
    args = parser.parse_args(argv)

    path = Path(args.env_file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    result = find_duplicates(path, env_name=args.name)
    print(_format_result(result))

    if args.exit_code and result.has_duplicates:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
