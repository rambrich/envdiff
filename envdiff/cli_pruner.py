"""CLI entry point for the pruner feature."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.pruner import PruneResult, prune_env


def _format_result(result: PruneResult, fmt: str) -> str:
    if fmt == "json":
        data = {
            "env_name": result.env_name,
            "pruned_count": result.pruned_count,
            "is_clean": result.is_clean,
            "records": [
                {"key": r.key, "value": r.value, "reason": r.reason}
                for r in result.records
            ],
            "output_env": result.output_env,
        }
        return json.dumps(data, indent=2)

    lines = [f"Prune report for: {result.env_name}"]
    if result.is_clean:
        lines.append("  No keys pruned — environment is clean.")
    else:
        for rec in result.records:
            lines.append(f"  [{rec.reason}] {rec.key}")
        lines.append(f"\n  Total pruned: {result.pruned_count}")
    return "\n".join(lines)


def build_pruner_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[name-defined]
    kwargs = dict(description="Prune obsolete or empty keys from an .env file.")
    parser = parent.add_parser("prune", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("env_file", help="Path to the .env file to prune.")
    parser.add_argument(
        "--reference",
        metavar="FILE",
        help="Reference .env file; keys absent from it are flagged as obsolete.",
    )
    parser.add_argument(
        "--keep-empty",
        action="store_true",
        help="Do not prune keys with empty values.",
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Do not prune duplicate values.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_pruner_parser()
    args = parser.parse_args(argv)

    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"Error: file not found: {env_path}", file=sys.stderr)
        return 2

    env = parse_env_file(str(env_path))

    reference_keys = None
    if args.reference:
        ref_path = Path(args.reference)
        if not ref_path.exists():
            print(f"Error: reference file not found: {ref_path}", file=sys.stderr)
            return 2
        reference_keys = list(parse_env_file(str(ref_path)).keys())

    result = prune_env(
        env,
        reference_keys=reference_keys,
        remove_empty=not args.keep_empty,
        remove_duplicates=not args.no_dedup,
        env_name=env_path.name,
    )

    print(_format_result(result, args.format))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
