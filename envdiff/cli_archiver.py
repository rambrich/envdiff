"""CLI entry-point for the archiver feature."""
from __future__ import annotations

import argparse
import sys

from envdiff.archiver import create_archive, load_archive


def _cmd_create(args: argparse.Namespace) -> int:
    result = create_archive(args.envfiles, args.output)
    print(f"Archive created: {result.path}")
    print(f"  Snapshots : {result.snapshot_count}")
    print(f"  Timestamp : {result.manifest.created_at}")
    for entry in result.manifest.entries:
        print(f"    - {entry}")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    try:
        snapshots = load_archive(args.archive)
    except FileNotFoundError:
        print(f"error: archive not found: {args.archive}", file=sys.stderr)
        return 2

    if not snapshots:
        print("Archive is empty.")
        return 0

    for name, snap in snapshots.items():
        print(f"{name}: {snap.key_count} key(s) captured at {snap.captured_at}")
    return 0


def build_archiver_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-archive",
        description="Archive and inspect .env snapshots.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Create a new archive from env files.")
    p_create.add_argument("envfiles", nargs="+", help=".env files to archive")
    p_create.add_argument("-o", "--output", required=True, help="Output .zip path")

    p_list = sub.add_parser("list", help="List snapshots inside an archive.")
    p_list.add_argument("archive", help="Path to the .zip archive")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_archiver_parser()
    args = parser.parse_args(argv)
    if args.command == "create":
        return _cmd_create(args)
    if args.command == "list":
        return _cmd_list(args)
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
