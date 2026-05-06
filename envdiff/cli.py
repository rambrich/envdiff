"""Command-line interface for envdiff."""

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.differ import diff_envs
from envdiff.reporter import print_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Diff .env files across environments and flag missing or mismatched keys.",
    )
    parser.add_argument(
        "source",
        metavar="SOURCE",
        help="Path to the source .env file (e.g. .env.example)",
    )
    parser.add_argument(
        "target",
        metavar="TARGET",
        help="Path to the target .env file (e.g. .env.production)",
    )
    parser.add_argument(
        "--no-values",
        action="store_true",
        default=False,
        help="Mask actual values in the report output",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if any issues are found",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    source_path = Path(args.source)
    target_path = Path(args.target)

    if not source_path.exists():
        print(f"envdiff: error: source file not found: {source_path}", file=sys.stderr)
        return 2

    if not target_path.exists():
        print(f"envdiff: error: target file not found: {target_path}", file=sys.stderr)
        return 2

    source_vars = parse_env_file(source_path)
    target_vars = parse_env_file(target_path)

    result = diff_envs(
        source_vars,
        target_vars,
        source_name=str(source_path),
        target_name=str(target_path),
    )

    print_report(result, mask_values=args.no_values)

    if args.exit_code and result.has_issues:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
