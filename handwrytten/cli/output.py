"""Shared output formatting helpers for the CLI."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Sequence

import click


def output_json_raw(data: Any) -> None:
    """Print raw JSON to stdout."""
    if hasattr(data, "raw"):
        data = data.raw
    elif isinstance(data, list) and data and hasattr(data[0], "raw"):
        data = [item.raw for item in data]
    click.echo(json.dumps(data, indent=2, default=str))


def print_table(
    rows: Sequence[Dict[str, Any]],
    columns: List[str],
    headers: Optional[List[str]] = None,
) -> None:
    """Print a simple formatted table to stdout.

    Args:
        rows: List of dicts (or objects with matching attrs).
        columns: Keys/attrs to display.
        headers: Optional display headers (defaults to column names).
    """
    if not rows:
        click.echo(click.style("  (no results)", dim=True))
        return

    headers = headers or [col.replace("_", " ").title() for col in columns]

    # Extract cell values
    str_rows = []
    for row in rows:
        cells = []
        for col in columns:
            if isinstance(row, dict):
                val = row.get(col, "")
            else:
                val = getattr(row, col, "")
            cells.append(str(val) if val is not None else "")
        str_rows.append(cells)

    # Calculate column widths
    widths = [len(h) for h in headers]
    for cells in str_rows:
        for i, cell in enumerate(cells):
            widths[i] = max(widths[i], len(cell))

    # Cap very wide columns
    max_col_width = 60
    widths = [min(w, max_col_width) for w in widths]

    # Print
    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    click.echo(click.style(header_line, bold=True))
    click.echo("  ".join("─" * w for w in widths))

    for cells in str_rows:
        line = "  ".join(cell[:widths[i]].ljust(widths[i]) for i, cell in enumerate(cells))
        click.echo(line)


def success(msg: str) -> None:
    """Print a green success message."""
    click.echo(click.style("✓ ", fg="green", bold=True) + msg)


def warn(msg: str) -> None:
    """Print a yellow warning."""
    click.echo(click.style("⚠ ", fg="yellow") + msg, err=True)


def error(msg: str) -> None:
    """Print a red error."""
    click.echo(click.style("✗ ", fg="red", bold=True) + msg, err=True)


def info(msg: str, quiet: bool = False) -> None:
    """Print an informational message (suppressed in quiet mode)."""
    if not quiet:
        click.echo(click.style("• ", dim=True) + msg, err=True)
