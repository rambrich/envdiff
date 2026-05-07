"""Command-line interface for envdiff."""

import argparse
import sys
from typing import List, Optional

from envdiff import diff_files
from envdiff.exporter import export_diff_result
from envdiff.filter import filter_diff_result
from envdiff.merger import MergeStrategy, merge_envs
from envdiff.parser import parse_env_file
from envdiff.reporter import format_report, print_report
from envdiff.sorter import sorted_diff_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Diff .env files across environments.",
    )
    parser.add_argument("source", help="Path to the source .env file")
    parser.add_argument("target", help="Path to the target .env file")
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when issues are found",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--filter-status",
        nargs="+",
        metavar="STATUS",
        help="Only show entries with these statuses (MATCH, MISMATCH, MISSING_IN_SOURCE, MISSING_IN_TARGET)",
    )
    parser.add_argument(
        "--filter-key",
        metavar="PATTERN",
        help="Only show keys matching this regex pattern",
    )
    parser.add_argument(
        "--sort",
        choices=["status", "key"],
        default="status",
        help="Sort entries by status (default) or key",
    )
    parser.add_argument(
        "--merge",
        nargs="+",
        metavar="FILE",
        help="Merge additional .env files using the specified strategy",
    )
    parser.add_argument(
        "--merge-strategy",
        choices=[s.value for s in MergeStrategy],
        default=MergeStrategy.FIRST.value,
        help="Strategy for resolving merge conflicts (default: first)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = diff_files(args.source, args.target)

    if args.filter_status or args.filter_key:
        result = filter_diff_result(
            result,
            statuses=args.filter_status or [],
            key_pattern=args.filter_key,
        )

    result = sorted_diff_result(result, sort_by=args.sort)

    if args.format == "text":
        print_report(result)
    else:
        print(export_diff_result(result, fmt=args.format))

    if args.exit_code and result.has_issues():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
