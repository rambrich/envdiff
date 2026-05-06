"""envdiff — diff .env files across environments."""

from envdiff.parser import parse_env_file
from envdiff.differ import diff_envs, DiffResult, DiffEntry, DiffStatus
from envdiff.reporter import format_report, print_report

__all__ = [
    "parse_env_file",
    "diff_envs",
    "DiffResult",
    "DiffEntry",
    "DiffStatus",
    "format_report",
    "print_report",
]

__version__ = "0.1.0"
