"""CLI entry-point for profiling one or two .env files."""

import argparse
import sys
from typing import Optional

from envdiff.differ import diff_envs
from envdiff.parser import parse_env_file
from envdiff.profiler import EnvProfile, profile_diff, profile_env


def _format_profile(profile: EnvProfile) -> str:
    lines = [
        f"Profile: {profile.env_name}",
        f"  Total keys      : {profile.total_keys}",
        f"  Empty values    : {profile.empty_count}  {profile.empty_value_keys}",
        f"  Numeric values  : {profile.numeric_count}  {profile.numeric_value_keys}",
        f"  Boolean values  : {profile.boolean_count}  {profile.boolean_value_keys}",
        f"  URL values      : {profile.url_count}  {profile.url_value_keys}",
    ]
    return "\n".join(lines)


def build_profile_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-profile",
        description="Profile one or two .env files and display value-type statistics.",
    )
    parser.add_argument("source", help="Path to the source .env file.")
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Optional path to a second .env file for a combined diff profile.",
    )
    parser.add_argument(
        "--source-name",
        default=None,
        help="Display name for the source environment (default: file path).",
    )
    parser.add_argument(
        "--target-name",
        default=None,
        help="Display name for the target environment (default: file path).",
    )
    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_profile_parser()
    args = parser.parse_args(argv)

    source_env = parse_env_file(args.source)
    source_name = args.source_name or args.source

    if args.target is None:
        profile = profile_env(source_env, env_name=source_name)
        print(_format_profile(profile))
        return 0

    target_env = parse_env_file(args.target)
    target_name = args.target_name or args.target

    result = diff_envs(source_env, target_env, source_name=source_name, target_name=target_name)
    dp = profile_diff(result)

    print(_format_profile(dp.source_profile))
    print()
    print(_format_profile(dp.target_profile))
    print()
    print("Diff overview:")
    print(f"  Keys in common  : {dp.overlap_count}")
    print(f"  Only in source  : {dp.unique_to_source}")
    print(f"  Only in target  : {dp.unique_to_target}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
