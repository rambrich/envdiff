"""CLI entry-point for the rename subcommand."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from envdiff.parser import parse_env_file
from envdiff.renamer import rename_keys


def _parse_mapping(pairs: List[str]) -> dict:
    """Convert a list of 'OLD=NEW' strings to a dict."""
    mapping: dict = {}
    for pair in pairs:
        if "=" not in pair:
            raise argparse.ArgumentTypeError(
                f"Invalid rename pair {pair!r}. Expected format: OLD_KEY=NEW_KEY"
            )
        old, new = pair.split("=", 1)
        mapping[old.strip()] = new.strip()
    return mapping


def _format_result(result) -> str:
    lines = [f"Rename summary: {result.applied_count} applied, {result.skipped_count} skipped"]
    for rec in result.records:
        tag = "OK" if rec.applied else "SKIP"
        lines.append(f"  [{tag}] {rec.old_key} -> {rec.new_key}")
    return "\n".join(lines)


def build_rename_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    kwargs = dict(description="Rename keys in a .env file.")
    if parent is not None:
        parser = parent.add_parser("rename", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument(
        "pairs",
        nargs="+",
        metavar="OLD=NEW",
        help="Key rename pairs in OLD=NEW format",
    )
    parser.add_argument("-o", "--output", help="Write renamed env to this file")
    parser.add_argument("--keep-old", action="store_true", help="Keep the original key alongside the new one")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output result as JSON")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_rename_parser()
    args = parser.parse_args(argv)

    try:
        mapping = _parse_mapping(args.pairs)
    except argparse.ArgumentTypeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    env = parse_env_file(args.env_file)
    result = rename_keys(env, mapping, remove_old=not args.keep_old)

    if args.as_json:
        print(json.dumps({"renamed": result.renamed, "records": [
            {"old_key": r.old_key, "new_key": r.new_key, "applied": r.applied}
            for r in result.records
        ]}, indent=2))
    else:
        print(_format_result(result))

    if args.output:
        lines = [f"{k}={v}" for k, v in result.renamed.items()]
        Path(args.output).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Written to {args.output}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
