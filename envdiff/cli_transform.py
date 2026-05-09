"""CLI entry-point for the transform sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envdiff.parser import parse_env_file
from envdiff.transformer import TransformOp, transform_env


def _format_result(result, *, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(
            {
                "env_name": result.env_name,
                "changed_count": result.changed_count,
                "output": result.output_env,
            },
            indent=2,
        )
    # default: key=value text
    lines = []
    for key, val in result.output_env.items():
        lines.append(f"{key}={val}" if val is not None else f"{key}=")
    return "\n".join(lines)


def build_transform_parser(parent: Optional[argparse._SubParsersAction] = None):
    description = "Transform .env key/value pairs."
    if parent is not None:
        p = parent.add_parser("transform", help=description)
    else:
        p = argparse.ArgumentParser(prog="envdiff-transform", description=description)

    p.add_argument("env_file", help="Path to the .env file to transform.")
    p.add_argument(
        "op",
        choices=[o.value for o in TransformOp],
        help="Transformation operation.",
    )
    p.add_argument("--prefix", default="", help="Prefix for add_prefix / remove_prefix ops.")
    p.add_argument("--value", default=None, help="Replacement value for set_value op.")
    p.add_argument(
        "--keys",
        nargs="+",
        default=None,
        metavar="KEY",
        help="Restrict transform to these keys only.",
    )
    p.add_argument("--name", default=None, help="Override env name in output.")
    p.add_argument(
        "--format",
        dest="fmt",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_transform_parser()
    args = parser.parse_args(argv)

    try:
        env = parse_env_file(args.env_file)
    except FileNotFoundError:
        print(f"error: file not found: {args.env_file}", file=sys.stderr)
        return 2

    env_name = args.name or args.env_file
    result = transform_env(
        env,
        TransformOp(args.op),
        prefix=args.prefix,
        value=args.value,
        keys=args.keys,
        env_name=env_name,
    )

    print(_format_result(result, fmt=args.fmt))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
