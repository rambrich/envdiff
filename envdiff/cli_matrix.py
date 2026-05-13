"""CLI entry-point for the diff-matrix command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from envdiff.differ_matrix import DiffMatrix, build_matrix
from envdiff.parser import parse_env_file


def _format_matrix(matrix: DiffMatrix) -> str:
    lines: List[str] = [
        f"Matrix: {matrix.source_name} vs {len(matrix.cells)} target(s)",
        "-" * 50,
    ]
    for cell in matrix.cells:
        status = "OK" if not cell.has_issues else "ISSUES"
        lines.append(f"  [{status}] {cell.target_name}")
        if cell.has_issues:
            for entry in cell.result.entries:
                if entry.status.name != "MATCH":
                    lines.append(f"         {entry.status.name}: {entry.key}")
    lines.append("-" * 50)
    lines.append(
        f"Clean: {len(matrix.clean_targets)}  "
        f"Failing: {len(matrix.failing_targets)}"
    )
    return "\n".join(lines)


def build_matrix_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-matrix",
        description="Diff one source .env against multiple target .env files.",
    )
    p.add_argument("source", help="Path to source .env file")
    p.add_argument("targets", nargs="+", help="Paths to target .env files")
    p.add_argument("--json", action="store_true", help="Output JSON")
    p.add_argument("--exit-code", action="store_true", help="Exit 1 if any issues found")
    return p


def main(argv: List[str] | None = None) -> int:
    parser = build_matrix_parser()
    args = parser.parse_args(argv)

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: source file not found: {source_path}", file=sys.stderr)
        return 2

    source_env = parse_env_file(source_path)
    targets: dict = {}
    for t in args.targets:
        tp = Path(t)
        if not tp.exists():
            print(f"Error: target file not found: {tp}", file=sys.stderr)
            return 2
        targets[tp.name] = parse_env_file(tp)

    matrix = build_matrix(source_env, targets, source_name=source_path.name)

    if args.json:
        out = {
            "source": matrix.source_name,
            "targets": [
                {
                    "name": cell.target_name,
                    "has_issues": cell.has_issues,
                    "entries": [
                        {"key": e.key, "status": e.status.name}
                        for e in cell.result.entries
                    ],
                }
                for cell in matrix.cells
            ],
        }
        print(json.dumps(out, indent=2))
    else:
        print(_format_matrix(matrix))

    if args.exit_code and matrix.has_any_issues:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
