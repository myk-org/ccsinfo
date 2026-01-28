"""Task management commands."""

from __future__ import annotations

from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ccsinfo.cli.state import state
from ccsinfo.core.client import get_client
from ccsinfo.core.models.tasks import TaskStatus
from ccsinfo.core.services import task_service as _task_service
from ccsinfo.utils.formatters import (
    create_table,
    print_error,
    print_json,
)

app = typer.Typer(help="Task management commands")
console = Console()


def _get_task_service() -> Any:
    """Get task_service instance."""
    return _task_service


_STATUS_DISPLAY_MAP = {
    "pending": "[yellow]pending[/]",
    "in_progress": "[blue]in_progress[/]",
    "completed": "[green]completed[/]",
}


def _status_to_display(status: str | TaskStatus) -> str:
    """Convert task status to display string with color."""
    status_str = status if isinstance(status, str) else status.value
    return _STATUS_DISPLAY_MAP.get(status_str, status_str)


@app.command("list")
def list_tasks(
    session: str | None = typer.Option(None, "--session", "-s", help="Filter by session ID"),
    status: str | None = typer.Option(None, "--status", "-t", help="Filter by status (pending/in_progress/completed)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """List all tasks."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        tasks_data = client.list_tasks(session_id=session, status=status)

        if json_output:
            print_json(tasks_data)
        else:
            if not tasks_data:
                console.print("[dim]No tasks found.[/dim]")
                return

            table = create_table(
                "Tasks",
                [
                    ("ID", "cyan"),
                    ("Subject", "green"),
                    ("Status", "yellow"),
                    ("Owner", "magenta"),
                    ("Blocked By", "red"),
                ],
            )
            for t in tasks_data:
                blocked_by_list = t.get("blocked_by", [])
                blocked_by = ", ".join(blocked_by_list) if blocked_by_list else "-"
                subject = t.get("subject", "")
                table.add_row(
                    t.get("id", ""),
                    subject[:40] + "..." if len(subject) > 40 else subject,
                    _status_to_display(t.get("status", "")),
                    t.get("owner") or "-",
                    blocked_by,
                )
            console.print(table)
    else:
        # Local mode - use services
        task_service = _get_task_service()

        # Convert status string to enum
        status_filter: TaskStatus | None = None
        if status:
            try:
                status_filter = TaskStatus(status.lower())
            except ValueError as e:
                print_error(f"Invalid status: {status}. Valid values: pending, in_progress, completed")
                raise typer.Exit(1) from e

        tasks = task_service.list_tasks(session_id=session, status=status_filter)

        if json_output:
            print_json([t.model_dump(mode="json") for t in tasks])
        else:
            if not tasks:
                console.print("[dim]No tasks found.[/dim]")
                return

            table = create_table(
                "Tasks",
                [
                    ("ID", "cyan"),
                    ("Subject", "green"),
                    ("Status", "yellow"),
                    ("Owner", "magenta"),
                    ("Blocked By", "red"),
                ],
            )
            for t in tasks:
                blocked_by = ", ".join(t.blocked_by) if t.blocked_by else "-"
                table.add_row(
                    t.id,
                    t.subject[:40] + "..." if len(t.subject) > 40 else t.subject,
                    _status_to_display(t.status),
                    t.owner or "-",
                    blocked_by,
                )
            console.print(table)


@app.command("show")
def show_task(
    task_id: str = typer.Argument(..., help="Task ID"),
    session: str = typer.Option(
        ..., "--session", "-s", help="Session ID (required since task IDs are only unique within a session)"
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show task details."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        try:
            task_data = client.get_task(task_id, session_id=session)
        except Exception:
            print_error(f"Task not found: {task_id}")
            raise typer.Exit(1) from None

        if json_output:
            print_json(task_data)
        else:
            title = f"Task: {task_data.get('id', '')}"
            content = Text()
            content.append("ID: ", style="bold")
            content.append(f"{task_data.get('id', '')}\n")
            content.append("Subject: ", style="bold")
            content.append(f"{task_data.get('subject', '')}\n")
            content.append("Description: ", style="bold")
            content.append(f"{task_data.get('description') or '(no description)'}\n")
            content.append("Status: ", style="bold")
            content.append(f"{task_data.get('status', '')}\n")
            content.append("Owner: ", style="bold")
            content.append(f"{task_data.get('owner') or '(unassigned)'}\n")
            content.append("Active Form: ", style="bold")
            content.append(f"{task_data.get('active_form') or '(none)'}\n")
            blocked_by_list = task_data.get("blocked_by", [])
            content.append("Blocked By: ", style="bold")
            content.append(f"{', '.join(blocked_by_list) if blocked_by_list else '(none)'}\n")
            blocks_list = task_data.get("blocks", [])
            content.append("Blocks: ", style="bold")
            content.append(f"{', '.join(blocks_list) if blocks_list else '(none)'}")

            metadata = task_data.get("metadata")
            if metadata:
                content.append("\nMetadata: ", style="bold")
                content.append(str(metadata))

            panel = Panel(content, title=title, border_style="cyan")
            console.print(panel)
    else:
        # Local mode - use services
        task_service = _get_task_service()
        task = task_service.get_task(task_id, session_id=session)

        if task is None:
            print_error(f"Task not found: {task_id}")
            raise typer.Exit(1)

        if json_output:
            print_json(task.model_dump(mode="json"))
        else:
            title = f"Task: {task.id}"
            content = Text()
            content.append("ID: ", style="bold")
            content.append(f"{task.id}\n")
            content.append("Subject: ", style="bold")
            content.append(f"{task.subject}\n")
            content.append("Description: ", style="bold")
            content.append(f"{task.description or '(no description)'}\n")
            content.append("Status: ", style="bold")
            content.append(f"{task.status}\n")
            content.append("Owner: ", style="bold")
            content.append(f"{task.owner or '(unassigned)'}\n")
            content.append("Active Form: ", style="bold")
            content.append(f"{task.active_form or '(none)'}\n")
            content.append("Blocked By: ", style="bold")
            content.append(f"{', '.join(task.blocked_by) if task.blocked_by else '(none)'}\n")
            content.append("Blocks: ", style="bold")
            content.append(f"{', '.join(task.blocks) if task.blocks else '(none)'}")

            if task.metadata:
                content.append("\nMetadata: ", style="bold")
                content.append(str(task.metadata))

            panel = Panel(content, title=title, border_style="cyan")
            console.print(panel)


@app.command("pending")
def pending_tasks(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show pending tasks."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        tasks_data = client.get_pending_tasks()

        if json_output:
            print_json(tasks_data)
        else:
            if not tasks_data:
                console.print("[dim]No pending tasks.[/dim]")
                return

            table = create_table(
                "Pending Tasks",
                [
                    ("ID", "cyan"),
                    ("Subject", "green"),
                    ("Owner", "magenta"),
                    ("Blocked By", "red"),
                ],
            )
            for t in tasks_data:
                blocked_by_list = t.get("blocked_by", [])
                blocked_by = ", ".join(blocked_by_list) if blocked_by_list else "-"
                subject = t.get("subject", "")
                table.add_row(
                    t.get("id", ""),
                    subject[:40] + "..." if len(subject) > 40 else subject,
                    t.get("owner") or "-",
                    blocked_by,
                )
            console.print(table)
    else:
        # Local mode - use services
        task_service = _get_task_service()
        tasks = task_service.get_pending_tasks()

        if json_output:
            print_json([t.model_dump(mode="json") for t in tasks])
        else:
            if not tasks:
                console.print("[dim]No pending tasks.[/dim]")
                return

            table = create_table(
                "Pending Tasks",
                [
                    ("ID", "cyan"),
                    ("Subject", "green"),
                    ("Owner", "magenta"),
                    ("Blocked By", "red"),
                ],
            )
            for t in tasks:
                blocked_by = ", ".join(t.blocked_by) if t.blocked_by else "-"
                table.add_row(
                    t.id,
                    t.subject[:40] + "..." if len(t.subject) > 40 else t.subject,
                    t.owner or "-",
                    blocked_by,
                )
            console.print(table)
