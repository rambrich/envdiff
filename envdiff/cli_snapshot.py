"""CLI entry point for snapshot capture and comparison."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.snapshotter import (
    capture_snapshot,
    save_snapshot,
    load_snapshot,
    diff_snapshots,
)


def _cmd_capture(args: argparse.Namespace) -> int:
    snapshot = capture_snapshot(args.env_file, name=args.name)
    dest = args.output or (Path(args.env_file).stem + ".snapshot.json")
    save_snapshot(snapshot, dest)
    print(f"Snapshot saved to {dest}  ({snapshot.key_count()} keys)")
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    old = load_snapshot(args.old)
    new = load_snapshot(args.new)
    changes = diff_snapshots(old, new)
    if not changes:
        print("No changes between snapshots.")
        return 0
    print(f"Changes between '{old.name}' and '{new.name}':")
    for key, (old_val, new_val) in changes.items():
        if old_val is None:
            print(f"  + {key} = {new_val}  (added)")
        elif new_val is None:
            print(f"  - {key}  (removed)")
        else:
            print(f"  ~ {key}: {old_val!r} -> {new_val!r}")
    if args.exit_code and changes:
        return 1
    return 0


def build_snapshot_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-snapshot",
        description="Capture and compare env file snapshots.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    cap = sub.add_parser("capture", help="Capture a snapshot of an env file.")
    cap.add_argument("env_file", help="Path to the .env file.")
    cap.add_argument("--name", default=None, help="Snapshot label.")
    cap.add_argument("--output", default=None, help="Output JSON path.")

    dif = sub.add_parser("diff", help="Diff two snapshots.")
    dif.add_argument("old", help="Path to the older snapshot JSON.")
    dif.add_argument("new", help="Path to the newer snapshot JSON.")
    dif.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when changes are found.",
    )

    return parser


def main(argv=None) -> int:
    parser = build_snapshot_parser()
    args = parser.parse_args(argv)
    if args.command == "capture":
        return _cmd_capture(args)
    return _cmd_diff(args)


if __name__ == "__main__":
    sys.exit(main())
