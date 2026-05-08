"""CLI entry-point for the 'score' sub-command."""
from __future__ import annotations

import argparse
import sys

from envdiff.parser import parse_env_file
from envdiff.differ import diff_envs
from envdiff.scorer import score_diff, DiffScore


def _format_score(ds: DiffScore) -> str:
    lines = [
        f"Source : {ds.source}",
        f"Target : {ds.target}",
        "-" * 36,
        f"Total keys           : {ds.total_keys}",
        f"Matches              : {ds.match_count}",
        f"Missing in target    : {ds.missing_in_target_count}",
        f"Missing in source    : {ds.missing_in_source_count}",
        f"Mismatches           : {ds.mismatch_count}",
        "-" * 36,
        f"Score  : {ds.score:.1f} / 100  [{ds.grade}]",
    ]
    return "\n".join(lines)


def build_score_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: E501
    kwargs = dict(
        description="Compute a health score for two .env files.",
    )
    if parent is not None:
        parser = parent.add_parser("score", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-score", **kwargs)

    parser.add_argument("source", help="Path to the source .env file")
    parser.add_argument("target", help="Path to the target .env file")
    parser.add_argument(
        "--mismatch-weight",
        type=float,
        default=0.5,
        metavar="W",
        help="Penalty weight for mismatched keys (0–1, default 0.5)",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        metavar="N",
        help="Exit with code 1 if score is below N",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_score_parser()
    args = parser.parse_args(argv)

    src_env = parse_env_file(args.source)
    tgt_env = parse_env_file(args.target)
    result = diff_envs(src_env, tgt_env, source_name=args.source, target_name=args.target)
    ds = score_diff(result, mismatch_weight=args.mismatch_weight)

    print(_format_score(ds))

    if args.min_score is not None and ds.score < args.min_score:
        print(
            f"\nFAIL: score {ds.score:.1f} is below minimum {args.min_score:.1f}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
