"""CLI sub-commands for baseline management (save / compare)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.baseline import Baseline, save_baseline, load_baseline, compare_to_baseline
from envdiff.parser import parse_env_file
from envdiff.reporter import print_report


def _cmd_save(args: argparse.Namespace) -> int:
    """Save an env file as a named baseline."""
    env = parse_env_file(Path(args.env_file))
    baseline = Baseline(
        name=args.name,
        env=env,
        description=args.description or "",
    )
    out_path = Path(args.output)
    save_baseline(baseline, out_path)
    print(f"Baseline '{args.name}' saved to {out_path}")
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    """Compare an env file against a saved baseline."""
    baseline = load_baseline(Path(args.baseline_file))
    current_env = parse_env_file(Path(args.env_file))
    result = compare_to_baseline(baseline, current_env, current_name=args.name)
    print_report(result)
    if args.exit_code and result.has_issues():
        return 1
    return 0


def build_baseline_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register baseline sub-commands onto an existing subparsers action."""
    # save
    save_p = subparsers.add_parser("baseline-save", help="Save env file as a baseline")
    save_p.add_argument("env_file", help="Path to the .env file")
    save_p.add_argument("--name", required=True, help="Baseline name")
    save_p.add_argument("--output", required=True, help="Output JSON path")
    save_p.add_argument("--description", default="", help="Optional description")
    save_p.set_defaults(func=_cmd_save)

    # compare
    cmp_p = subparsers.add_parser("baseline-compare", help="Compare env file against a baseline")
    cmp_p.add_argument("baseline_file", help="Path to baseline JSON")
    cmp_p.add_argument("env_file", help="Path to the current .env file")
    cmp_p.add_argument("--name", default="current", help="Label for the current env")
    cmp_p.add_argument("--exit-code", action="store_true", help="Exit 1 when issues found")
    cmp_p.set_defaults(func=_cmd_compare)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="envdiff-baseline", description="Baseline management")
    subparsers = parser.add_subparsers(dest="command")
    build_baseline_parser(subparsers)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
