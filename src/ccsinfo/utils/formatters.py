"""Output formatting utilities using Rich."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import orjson
import pendulum
from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from datetime import datetime

console = Console()


def format_datetime(dt: datetime | str | None) -> str:
    """Format a datetime for display.

    Handles both datetime objects (from local mode) and ISO format strings
    (from remote server mode).
    """
    if dt is None:
        return "N/A"
    if isinstance(dt, str):
        parsed = pendulum.parse(dt)
        if parsed is None:
            return "N/A"
        formatted: str = parsed.strftime("%Y-%m-%d %H:%M:%S")
        return formatted
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_relative_time(dt: datetime | str | None) -> str:
    """Format a datetime as relative time (e.g., '2 hours ago').

    Handles both datetime objects (from local mode) and ISO format strings
    (from remote server mode).
    """
    if dt is None:
        return "N/A"
    if isinstance(dt, str):
        parsed = pendulum.parse(dt)
        if parsed is None:
            return "N/A"
        result: str = parsed.diff_for_humans()
        return result
    result_inst: str = pendulum.instance(dt).diff_for_humans()
    return result_inst


def create_table(title: str, columns: list[tuple[str, str]]) -> Table:
    """Create a Rich table with the given columns.

    Args:
        title: The table title.
        columns: A list of (column_name, style) tuples.

    Returns:
        A Rich Table instance with the specified columns.
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for name, style in columns:
        table.add_column(name, style=style)
    return table


def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    console.print_json(orjson.dumps(data).decode())


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]\u2713[/bold green] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")
