"""CLI entry-point for the comparator-chain command."""
from __future__ import annotations

import argparse
import sys

from envdiff.comparator_chain import build_chain
from envdiff.differ import diff_envs
from envdiff.filter import filter_diff_result
from envdiff.parser import parse_env_file
from envdiff.sorter import sorted_diff_result


def _format_chain_result(cr) -> str:
    lines = [
        f"Source : {cr.source}",
        f"Target : {cr.target}",
        f"Steps  : {', '.join(cr.step_names) or '(none)'}",
        f"Entries: {len(cr.result.entries)}",
        f"Issues : {'yes' if cr.has_issues else 'no'}",
        "",
    ]
    for entry in cr.result.entries:
        lines.append(f"  [{entry.status.value}] {entry.key}")
    return "\n".join(lines)


def build_chain_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-chain",
        description="Run a diff through a configurable step chain.",
    )
    p.add_argument("source", help="Source .env file")
    p.add_argument("target", help="Target .env file")
    p.add_argument(
        "--filter",
        dest="statuses",
        nargs="+",
        default=[],
        metavar="STATUS",
        help="Filter entries by status (e.g. missing_in_target mismatch)",
    )
    p.add_argument(
        "--sort",
        choices=["status", "key"],
        default=None,
        help="Sort entries by status or key after filtering",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when issues are found",
    )
    return p


def main(argv=None) -> int:
    parser = build_chain_parser()
    args = parser.parse_args(argv)

    try:
        src_env = parse_env_file(args.source)
        tgt_env = parse_env_file(args.target)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    diff = diff_envs(src_env, tgt_env)

    steps = []
    if args.statuses:
        steps.append(("filter", lambda d: filter_diff_result(d, statuses=args.statuses)))
    if args.sort == "status":
        steps.append(("sort_by_status", lambda d: sorted_diff_result(d, by="status")))
    elif args.sort == "key":
        steps.append(("sort_by_key", lambda d: sorted_diff_result(d, by="key")))

    chain = build_chain(*steps)
    cr = chain.run(diff)

    print(_format_chain_result(cr))

    if args.exit_code and cr.has_issues:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
