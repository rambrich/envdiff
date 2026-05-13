"""CLI entry point for computing cross-diff key frequency statistics."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.differ_stats import compute_diff_stats, DiffStatsResult
from envdiff.differ import diff_envs
from envdiff.parser import parse_env_file


def _format_stats(stats: DiffStatsResult, fmt: str) -> str:
    if fmt == "json":
        data = {
            "diff_count": stats.diff_count,
            "most_volatile_key": stats.most_volatile_key,
            "stable_keys": stats.stable_keys,
            "key_frequencies": [
                {
                    "key": kf.key,
                    "total": kf.total,
                    "most_common_status": kf.most_common_status,
                    "status_counts": kf.status_counts,
                }
                for kf in stats.key_frequencies
            ],
        }
        return json.dumps(data, indent=2)

    lines: List[str] = []
    lines.append(f"Diffs analysed : {stats.diff_count}")
    lines.append(f"Most volatile  : {stats.most_volatile_key or 'N/A'}")
    lines.append(f"Stable keys    : {', '.join(stats.stable_keys) or 'none'}")
    lines.append("")
    lines.append(f"{'KEY':<30} {'TOTAL':>5}  {'MOST COMMON STATUS'}")
    lines.append("-" * 55)
    for kf in stats.key_frequencies:
        lines.append(f"{kf.key:<30} {kf.total:>5}  {kf.most_common_status}")
    return "\n".join(lines)


def build_stats_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-stats",
        description="Compute key-change frequency statistics across multiple env comparisons.",
    )
    parser.add_argument("source", help="Source .env file (the reference environment).")
    parser.add_argument(
        "targets", nargs="+", help="One or more target .env files to compare."
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_stats_parser()
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
        results.append(
            diff_envs(source_env, target_env, source_name=args.source, target_name=target_path)
        )

    stats = compute_diff_stats(results)
    print(_format_stats(stats, args.format))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
