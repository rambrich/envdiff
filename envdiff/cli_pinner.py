"""CLI entry-point for the pin-checker."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.parser import parse_env_file
from envdiff.pinner import PinResult, check_pins


def _format_result(result: PinResult, fmt: str) -> str:
    if fmt == "json":
        data = {
            "env_name": result.env_name,
            "is_pinned": result.is_pinned,
            "violation_count": result.violation_count,
            "violations": [
                {
                    "key": v.key,
                    "pinned_value": v.pinned_value,
                    "actual_value": v.actual_value,
                }
                for v in result.violations
            ],
        }
        return json.dumps(data, indent=2)

    lines: List[str] = [f"Env : {result.env_name}"]
    if result.is_pinned:
        lines.append("Status: all pins match ✓")
    else:
        lines.append(f"Status: {result.violation_count} violation(s) detected")
        for v in result.violations:
            actual_display = v.actual_value if v.actual_value is not None else "<missing>"
            lines.append(
                f"  [{v.key}]  pinned={v.pinned_value!r}  actual={actual_display!r}"
            )
    return "\n".join(lines)


def build_pin_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-pin",
        description="Check that specific keys in an .env file match pinned values.",
    )
    p.add_argument("env_file", help="Path to the .env file to check.")
    p.add_argument(
        "pins",
        nargs="+",
        metavar="KEY=VALUE",
        help="Pinned key=value pairs, e.g. APP_ENV=production.",
    )
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when violations are found.",
    )
    return p


def main(argv=None) -> int:
    parser = build_pin_parser()
    args = parser.parse_args(argv)

    try:
        env = parse_env_file(args.env_file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.env_file}", file=sys.stderr)
        return 2

    pins: dict[str, str] = {}
    for pair in args.pins:
        if "=" not in pair:
            print(f"Error: invalid pin {pair!r} — expected KEY=VALUE", file=sys.stderr)
            return 2
        k, _, v = pair.partition("=")
        pins[k.strip()] = v.strip()

    result = check_pins(env, pins, env_name=args.env_file)
    print(_format_result(result, args.format))

    if args.exit_code and not result.is_pinned:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
