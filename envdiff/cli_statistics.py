"""CLI entry point for the statistics command."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.differ import diff
from envdiff.parser import parse_env_file
from envdiff.statistics import EnvStatistics, compute_statistics


def _format_statistics(stats: EnvStatistics) -> str:
    lines: List[str] = [
        f"Comparisons : {stats.total_comparisons}",
        f"Total entries: {stats.total_entries}",
        f"Unique keys  : {len(stats.unique_keys)}",
        f"Matches      : {stats.total_matches}",
        f"Mismatches   : {stats.total_mismatches}",
        f"Missing/target: {stats.total_missing_in_target}",
        f"Missing/source: {stats.total_missing_in_source}",
        f"Match rate   : {stats.match_rate:.1%}",
        f"Issue rate   : {stats.issue_rate:.1%}",
    ]
    return "\n".join(lines)


def build_statistics_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-statistics",
        description="Compute aggregate statistics across multiple env file comparisons.",
    )
    parser.add_argument("source", help="Source .env file (baseline)")
    parser.add_argument(
        "targets", nargs="+", help="One or more target .env files to compare against source"
    )
    parser.add_argument(
        "--json", dest="as_json", action="store_true", help="Output as JSON"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_statistics_parser()
    args = parser.parse_args(argv)

    try:
        source_env = parse_env_file(args.source)
    except FileNotFoundError:
        print(f"Error: source file not found: {args.source}", file=sys.stderr)
        return 2

    results = []
    for target_path in args.targets:
        try:
            target_env = parse_env_file(target_path)
        except FileNotFoundError:
            print(f"Error: target file not found: {target_path}", file=sys.stderr)
            return 2
        results.append(diff(source_env, target_env, source_name=args.source, target_name=target_path))

    stats = compute_statistics(results)

    if args.as_json:
        print(json.dumps({
            "total_comparisons": stats.total_comparisons,
            "total_entries": stats.total_entries,
            "unique_keys": stats.unique_keys,
            "total_matches": stats.total_matches,
            "total_mismatches": stats.total_mismatches,
            "total_missing_in_target": stats.total_missing_in_target,
            "total_missing_in_source": stats.total_missing_in_source,
            "match_rate": round(stats.match_rate, 4),
            "issue_rate": round(stats.issue_rate, 4),
        }, indent=2))
    else:
        print(_format_statistics(stats))

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
