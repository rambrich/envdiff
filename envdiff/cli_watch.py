"""CLI entry-point for the ``envdiff watch`` command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.watcher import watch, WatchEvent
from envdiff.reporter import format_report


def _on_change(event: WatchEvent, *, quiet: bool) -> None:
    """Default callback: print a report to stdout."""
    timestamp_line = f"[changed] {event.path}"
    print(timestamp_line)
    if quiet:
        status = "issues detected" if event.diff.has_issues() else "no issues"
        print(f"  {status}")
    else:
        report = format_report(event.diff)
        print(report)
    print()


def _validate_files(source: Path, target: Path) -> str | None:
    """Validate that both source and target files exist.

    Returns an error message string if validation fails, or ``None`` if both
    files are present and readable.
    """
    if not source.exists():
        return f"error: source file not found: {source}"
    if not target.exists():
        return f"error: target file not found: {target}"
    return None


def build_watch_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs: dict = dict(
        description="Watch .env files and print a diff whenever they change."
    )
    if parent is not None:
        parser = parent.add_parser("watch", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-watch", **kwargs)

    parser.add_argument("source", type=Path, help="Reference .env file.")
    parser.add_argument("target", type=Path, help="Target .env file to watch.")
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 1.0).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print a one-line status instead of the full report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_watch_parser()
    args = parser.parse_args(argv)

    error = _validate_files(args.source, args.target)
    if error is not None:
        print(error, file=sys.stderr)
        return 2

    print(f"Watching {args.target} (against {args.source}) — press Ctrl+C to stop.")
    print()

    try:
        watch(
            args.source,
            args.target,
            callback=lambda ev: _on_change(ev, quiet=args.quiet),
            interval=args.interval,
        )
    except KeyboardInterrupt:
        print("\nStopped.")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
