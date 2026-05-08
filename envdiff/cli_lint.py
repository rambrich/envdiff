"""CLI entry point for the envdiff lint command."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.linter import lint_env_file, LintSeverity, LintResult


def _format_result(result: LintResult) -> str:
    lines: List[str] = []
    lines.append(f"Lint results for: {result.env_name}")
    if result.is_clean:
        lines.append("  No issues found. ✓")
        return "\n".join(lines)

    for issue in result.issues:
        icon = "✗" if issue.severity == LintSeverity.ERROR else "⚠"
        key_part = f" [{issue.key}]" if issue.key else ""
        lines.append(f"  {icon} Line {issue.line_number}{key_part}: {issue.message}")

    lines.append("")
    lines.append(
        f"  Summary: {result.error_count} error(s), {result.warning_count} warning(s)"
    )
    return "\n".join(lines)


def build_lint_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    if parser is None:
        parser = argparse.ArgumentParser(
            prog="envdiff-lint",
            description="Lint a .env file for style and formatting issues.",
        )
    parser.add_argument("env_file", help="Path to the .env file to lint")
    parser.add_argument(
        "--name",
        default=None,
        help="Display name for the environment (defaults to file path)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any warnings are present (not just errors)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_lint_parser()
    args = parser.parse_args(argv)

    result = lint_env_file(args.env_file, env_name=args.name)
    print(_format_result(result))

    if result.error_count > 0:
        return 1
    if args.strict and result.warning_count > 0:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
