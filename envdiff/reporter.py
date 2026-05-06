"""Format and render DiffResult objects for human-readable output."""

from typing import TextIO
import sys

from envdiff.differ import DiffResult, DiffStatus

_STATUS_SYMBOLS = {
    DiffStatus.MISSING_IN_TARGET: "✗ MISSING IN TARGET",
    DiffStatus.MISSING_IN_SOURCE: "✗ MISSING IN SOURCE",
    DiffStatus.VALUE_MISMATCH: "~ MISMATCH",
    DiffStatus.OK: "✓ OK",
}


def format_report(result: DiffResult, show_ok: bool = False) -> str:
    """Return a formatted string report of the diff result."""
    lines = [
        f"Comparing '{result.source_name}' → '{result.target_name}'",
        "-" * 50,
    ]

    for entry in result.entries:
        if entry.status == DiffStatus.OK and not show_ok:
            continue

        label = _STATUS_SYMBOLS[entry.status]
        line = f"  [{label}] {entry.key}"

        if entry.status == DiffStatus.VALUE_MISMATCH:
            line += f"\n      source : {entry.source_value!r}"
            line += f"\n      target : {entry.target_value!r}"
        elif entry.status == DiffStatus.MISSING_IN_TARGET:
            line += f"  (source value: {entry.source_value!r})"
        elif entry.status == DiffStatus.MISSING_IN_SOURCE:
            line += f"  (target value: {entry.target_value!r})"

        lines.append(line)

    lines.append("-" * 50)

    summary_parts = []
    if result.missing_in_target:
        summary_parts.append(f"{len(result.missing_in_target)} missing in target")
    if result.missing_in_source:
        summary_parts.append(f"{len(result.missing_in_source)} missing in source")
    if result.mismatched:
        summary_parts.append(f"{len(result.mismatched)} mismatched")

    if summary_parts:
        lines.append("Summary: " + ", ".join(summary_parts))
    else:
        lines.append("Summary: all keys match")

    return "\n".join(lines)


def print_report(result: DiffResult, show_ok: bool = False, file: TextIO = sys.stdout) -> None:
    """Print the formatted report to a file-like object (default: stdout)."""
    print(format_report(result, show_ok=show_ok), file=file)
