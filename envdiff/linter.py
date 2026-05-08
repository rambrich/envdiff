"""Linter for .env files — checks for common style and formatting issues."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class LintSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass
class LintIssue:
    line_number: int
    key: str
    message: str
    severity: LintSeverity

    def __repr__(self) -> str:
        return f"LintIssue(line={self.line_number}, key={self.key!r}, severity={self.severity.value}, message={self.message!r})"


@dataclass
class LintResult:
    env_name: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == LintSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == LintSeverity.WARNING)


def lint_env_file(path: str, env_name: str | None = None) -> LintResult:
    """Lint a .env file and return a LintResult with any issues found."""
    name = env_name or path
    result = LintResult(env_name=name)

    with open(path, "r") as f:
        lines = f.readlines()

    for lineno, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\n")

        # Skip blank lines and comments
        if not line.strip() or line.strip().startswith("#"):
            continue

        if "=" not in line:
            result.issues.append(LintIssue(
                line_number=lineno,
                key="",
                message="Line is not a valid KEY=VALUE pair",
                severity=LintSeverity.ERROR,
            ))
            continue

        key, _, value = line.partition("=")

        if key != key.strip():
            result.issues.append(LintIssue(
                line_number=lineno,
                key=key.strip(),
                message="Key has leading or trailing whitespace",
                severity=LintSeverity.WARNING,
            ))

        if key.strip() != key.strip().upper():
            result.issues.append(LintIssue(
                line_number=lineno,
                key=key.strip(),
                message="Key is not uppercase",
                severity=LintSeverity.WARNING,
            ))

        if not key.strip():
            result.issues.append(LintIssue(
                line_number=lineno,
                key="",
                message="Empty key",
                severity=LintSeverity.ERROR,
            ))

        stripped_value = value.strip()
        if (
            len(stripped_value) >= 2
            and stripped_value[0] in ('"', "'")
            and stripped_value[-1] == stripped_value[0]
        ):
            result.issues.append(LintIssue(
                line_number=lineno,
                key=key.strip(),
                message="Value is wrapped in quotes; consider storing raw values",
                severity=LintSeverity.WARNING,
            ))

    return result
