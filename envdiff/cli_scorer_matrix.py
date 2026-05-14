"""CLI entry-point: score a source .env against multiple target files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ_matrix import build_matrix
from envdiff.parser import parse_env_file
from envdiff.scorer_matrix import MatrixScoreResult, score_matrix


def _format_result(result: MatrixScoreResult) -> str:
    lines: list[str] = [
        f"Source : {result.source_name}",
        f"Average: {result.average_score:.1f}",
        "-" * 40,
    ]
    for entry in sorted(result.entries, key=lambda e: e.score.score):
        lines.append(
            f"  {entry.target_name:<30} {entry.score.score:6.1f}  [{entry.score.grade}]"
        )
    if result.lowest_entry:
        lines.append("-" * 40)
        lines.append(f"Lowest : {result.lowest_entry.target_name} ({result.lowest_entry.score.score:.1f})")
    return "\n".join(lines)


def build_scorer_matrix_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-score-matrix",
        description="Score a source .env file against one or more target .env files.",
    )
    p.add_argument("source", help="Path to the source .env file")
    p.add_argument("targets", nargs="+", help="Paths to one or more target .env files")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_scorer_matrix_parser()
    args = parser.parse_args(argv)

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"error: source file not found: {source_path}", file=sys.stderr)
        return 2

    target_paths: list[Path] = []
    for t in args.targets:
        p = Path(t)
        if not p.exists():
            print(f"error: target file not found: {p}", file=sys.stderr)
            return 2
        target_paths.append(p)

    source_env = parse_env_file(source_path)
    target_envs = [parse_env_file(p) for p in target_paths]

    matrix = build_matrix(source_env, target_envs)
    result = score_matrix(matrix)

    if args.json:
        import json
        data = {
            "source": result.source_name,
            "average_score": round(result.average_score, 2),
            "targets": [
                {"name": e.target_name, "score": e.score.score, "grade": e.score.grade}
                for e in result.entries
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        print(_format_result(result))

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
