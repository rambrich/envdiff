"""CLI entry point for the auditor module."""
from __future__ import annotations

import argparse
import json
import sys

from envdiff.auditor import audit_diff_result
from envdiff.differ import diff_envs
from envdiff.parser import parse_env_file


def _format_log(log, fmt: str) -> str:
    if fmt == "json":
        data = {
            "env_name": log.env_name,
            "entry_count": log.entry_count,
            "entries": [
                {
                    "timestamp": e.timestamp,
                    "operation": e.operation,
                    "source": e.source,
                    "target": e.target,
                    "key": e.key,
                    "detail": e.detail,
                }
                for e in log.entries
            ],
        }
        return json.dumps(data, indent=2)
    lines = [f"Audit Log: {log.env_name}", f"Entries : {log.entry_count}", ""]
    for e in log.entries:
        lines.append(f"  [{e.operation.upper():22s}] {e.key}  —  {e.detail}")
    return "\n".join(lines)


def build_audit_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-audit",
        description="Generate an audit log for a diff between two .env files.",
    )
    p.add_argument("source", help="Source .env file")
    p.add_argument("target", help="Target .env file")
    p.add_argument("--name", default="audit", help="Label for the audit log")
    p.add_argument(
        "--format", choices=["text", "json"], default="text", dest="fmt"
    )
    return p


def main(argv=None) -> int:
    parser = build_audit_parser()
    args = parser.parse_args(argv)

    try:
        source_env = parse_env_file(args.source)
        target_env = parse_env_file(args.target)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    result = diff_envs(source_env, target_env, source_name=args.source, target_name=args.target)
    log = audit_diff_result(result, env_name=args.name)
    print(_format_log(log, args.fmt))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
