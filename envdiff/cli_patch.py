"""CLI entry-point for the `envdiff patch` command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ import diff_envs
from envdiff.parser import parse_env_file
from envdiff.patcher import PatchAction, patch_env


def _write_env(env: dict, path: Path) -> None:
    lines = [f"{k}={v}\n" for k, v in env.items()]
    path.write_text("".join(lines), encoding="utf-8")


def build_patch_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    if parser is None:
        parser = argparse.ArgumentParser(
            prog="envdiff-patch",
            description="Patch a target .env file using keys from a source .env file.",
        )
    parser.add_argument("source", help="Source .env file (authoritative)")
    parser.add_argument("target", help="Target .env file to patch")
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write patched env to this file (default: overwrite target)",
    )
    parser.add_argument(
        "--apply-mismatch",
        action="store_true",
        default=False,
        help="Also overwrite mismatched values in target with source values",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print what would change without writing any file",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_patch_parser()
    args = parser.parse_args(argv)

    source_env = parse_env_file(args.source)
    target_env = parse_env_file(args.target)

    diff = diff_envs(
        source_env,
        target_env,
        source_name=args.source,
        target_name=args.target,
    )

    result = patch_env(
        target_env,
        diff,
        apply_missing=True,
        apply_mismatch=args.apply_mismatch,
    )

    for record in result.records:
        if record.action == PatchAction.ADDED:
            print(f"[ADD]    {record.key}={record.new_value}")
        elif record.action == PatchAction.UPDATED:
            print(f"[UPDATE] {record.key}: {record.old_value!r} -> {record.new_value!r}")
        elif record.action == PatchAction.SKIPPED:
            print(f"[SKIP]   {record.key}")

    if args.dry_run:
        print("Dry-run mode: no files written.")
        return 0

    out_path = Path(args.output) if args.output else Path(args.target)
    _write_env(result.patched_env, out_path)
    print(f"Patched env written to {out_path} ({result.applied_count} change(s)).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
