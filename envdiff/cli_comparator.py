"""CLI entry-point for multi-env comparison."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.comparator import compare_many
from envdiff.parser import parse_env_file
from envdiff.reporter import format_report


def _format_compare_result(compare_result) -> str:
    lines: list[str] = [
        f"Source: {compare_result.source_name}",
        f"Targets compared: {len(compare_result.target_names)}",
        "-" * 48,
    ]
    for target_name, diff_result in compare_result.results.items():
        summary = compare_result.summaries[target_name]
        lines.append(f"\n[{target_name}]")
        lines.append(
            f"  match={summary.match_count}  missing_in_target={summary.missing_in_target_count}"
            f"  missing_in_source={summary.missing_in_source_count}  mismatch={summary.mismatch_count}"
        )
        if diff_result.has_issues():
            lines.append(format_report(diff_result))
        else:
            lines.append("  No issues found.")
    worst = compare_result.worst_target()
    if worst and compare_result.has_any_issues():
        lines.append(f"\nWorst target: {worst}")
    return "\n".join(lines)


def build_comparator_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-compare",
        description="Compare one source .env against multiple target .env files.",
    )
    p.add_argument("source", help="Path to the source .env file.")
    p.add_argument("targets", nargs="+", help="Paths to one or more target .env files.")
    p.add_argument("--exit-code", action="store_true", help="Exit 1 when issues are found.")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_comparator_parser()
    args = parser.parse_args(argv)

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: source file not found: {source_path}", file=sys.stderr)
        return 2

    source_env = parse_env_file(source_path)
    targets: dict[str, dict[str, str]] = {}
    for t in args.targets:
        tp = Path(t)
        if not tp.exists():
            print(f"Error: target file not found: {tp}", file=sys.stderr)
            return 2
        targets[tp.name] = parse_env_file(tp)

    result = compare_many(source_env, targets, source_name=source_path.name)
    print(_format_compare_result(result))

    if args.exit_code and result.has_any_issues():
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
