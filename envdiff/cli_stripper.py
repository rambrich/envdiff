"""CLI entry-point for the env key stripper."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.stripper import strip_keys


def _format_result(result) -> str:
    lines = [f"Stripper — {result.env_name}"]
    lines.append(f"  Keys retained : {len(result.output_env)}")
    lines.append(f"  Keys stripped : {result.stripped_count}")
    if result.stripped:
        lines.append("  Stripped keys:")
        for rec in result.stripped:
            lines.append(f"    - {rec.key}  ({rec.reason})")
    return "\n".join(lines)


def build_stripper_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-strip",
        description="Remove keys from TARGET that are absent in SOURCE.",
    )
    p.add_argument("source", help="Reference .env file (defines allowed keys)")
    p.add_argument("target", help=".env file to strip")
    p.add_argument("--json", action="store_true", help="Output JSON")
    p.add_argument(
        "--write",
        metavar="FILE",
        help="Write stripped env to FILE instead of stdout",
    )
    return p


def main(argv=None) -> int:
    parser = build_stripper_parser()
    args = parser.parse_args(argv)

    source_path = Path(args.source)
    target_path = Path(args.target)

    for p in (source_path, target_path):
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2

    reference = parse_env_file(source_path)
    target_env = parse_env_file(target_path)

    result = strip_keys(target_env, reference, env_name=target_path.name)

    if args.write:
        out_path = Path(args.write)
        lines = [f"{k}={v}" for k, v in result.output_env.items()]
        out_path.write_text("\n".join(lines) + "\n")

    if args.json:
        payload = {
            "env_name": result.env_name,
            "stripped_count": result.stripped_count,
            "output_env": result.output_env,
            "stripped": [{"key": r.key, "value": r.value, "reason": r.reason} for r in result.stripped],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(_format_result(result))

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
