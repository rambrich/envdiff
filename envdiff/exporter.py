"""Export diff results to various output formats (JSON, CSV)."""

from __future__ import annotations

import csv
import io
import json
from typing import Literal

from envdiff.differ import DiffResult

OutputFormat = Literal["json", "csv"]


def export_to_json(result: DiffResult, indent: int = 2) -> str:
    """Serialize a DiffResult to a JSON string."""
    data = {
        "source": result.source_name,
        "target": result.target_name,
        "entries": [
            {
                "key": entry.key,
                "status": entry.status.value,
                "source_value": entry.source_value,
                "target_value": entry.target_value,
            }
            for entry in result.entries
        ],
    }
    return json.dumps(data, indent=indent)


def export_to_csv(result: DiffResult) -> str:
    """Serialize a DiffResult to a CSV string."""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["key", "status", "source_value", "target_value"],
        lineterminator="\n",
    )
    writer.writeheader()
    for entry in result.entries:
        writer.writerow(
            {
                "key": entry.key,
                "status": entry.status.value,
                "source_value": entry.source_value if entry.source_value is not None else "",
                "target_value": entry.target_value if entry.target_value is not None else "",
            }
        )
    return output.getvalue()


def export_diff_result(result: DiffResult, fmt: OutputFormat) -> str:
    """Export a DiffResult to the requested format.

    Args:
        result: The diff result to export.
        fmt: One of ``'json'`` or ``'csv'``.

    Returns:
        Serialized string in the requested format.

    Raises:
        ValueError: If *fmt* is not a supported format.
    """
    if fmt == "json":
        return export_to_json(result)
    if fmt == "csv":
        return export_to_csv(result)
    raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'json' or 'csv'.")
