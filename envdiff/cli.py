"""Command-line interface for envdiff."""

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.differ import diff
from envdiff.reporter import print_report
from envdiff.sorter import sorted_diff_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Diff .env files across environments and flag missing or mismatched keys.",
    )
    parser.add_argument("source", type=Path, help="Source .env file (e.g. .env.dev)")
    parser.add_argument("target", type=Path, help="Target .env file (e.g. .env.prod)")
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if there are any issues (missing or mismatched keys).",
    )
    parser.add_argument(
        "--sort",
        choices=["status", "key"],
        default="status",
        help="Sort output entries by 'status' (default) or 'key'.",
    )
    parser.add_argument(
        "--no-ok",
        action="store_true",
        default=False,
        help="Hide keys that match between source and target.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    source_path: Path = args.source
    target_path: Path = args.target

    if not source_path.exists():
        print(f"Error: source file '{source_path}' does not exist.", file=sys.stderr)
        return 2

    if not target_path.exists():
        print(f"Error: target file '{target_path}' does not exist.", file=sys.stderr)
        return 2

    source_env = parse_env_file(source_path)
    target_env = parse_env_file(target_path)

    result = diff(
        source_env,
        target_env,
        source_name=str(source_path),
        target_name=str(target_path),
    )

    result = sorted_diff_result(result, by=args.sort)

    if args.no_ok:
        from envdiff.differ import DiffStatus
        result.entries = [e for e in result.entries if e.status != DiffStatus.OK]

    print_report(result)

    if args.exit_code and result.has_issues():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
