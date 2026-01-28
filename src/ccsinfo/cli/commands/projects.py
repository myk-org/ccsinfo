"""Project management commands."""

from __future__ import annotations

from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ccsinfo.cli.state import state
from ccsinfo.core.client import get_client
from ccsinfo.core.services import project_service as _project_service
from ccsinfo.utils.formatters import (
    create_table,
    format_datetime,
    format_relative_time,
    print_error,
    print_json,
)

app = typer.Typer(help="Project management commands")
console = Console()


def _get_project_service() -> Any:
    """Get project_service instance."""
    return _project_service


@app.command("list")
def list_projects(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """List all projects."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        projects_data = client.list_projects()

        if json_output:
            print_json(projects_data)
        else:
            if not projects_data:
                console.print("[dim]No projects found.[/dim]")
                return

            table = create_table(
                "Projects",
                [
                    ("ID", "cyan"),
                    ("Name", "green"),
                    ("Sessions", "yellow"),
                    ("Last Activity", "magenta"),
                ],
            )
            for p in projects_data:
                pid = p.get("id", "")
                table.add_row(
                    pid[:16] + "..." if len(pid) > 16 else pid,
                    p.get("name", ""),
                    str(p.get("session_count", 0)),
                    format_relative_time(p.get("last_activity")),
                )
            console.print(table)
    else:
        # Local mode - use services
        project_service = _get_project_service()
        projects = project_service.list_projects()

        if json_output:
            print_json([p.model_dump(mode="json") for p in projects])
        else:
            if not projects:
                console.print("[dim]No projects found.[/dim]")
                return

            table = create_table(
                "Projects",
                [
                    ("ID", "cyan"),
                    ("Name", "green"),
                    ("Sessions", "yellow"),
                    ("Last Activity", "magenta"),
                ],
            )
            for p in projects:
                table.add_row(
                    p.id[:16] + "..." if len(p.id) > 16 else p.id,
                    p.name,
                    str(p.session_count),
                    format_relative_time(p.last_activity),
                )
            console.print(table)


@app.command("show")
def show_project(
    project_id: str = typer.Argument(..., help="Project ID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show project details."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        try:
            project_data = client.get_project(project_id)
        except Exception:
            print_error(f"Project not found: {project_id}")
            raise typer.Exit(1) from None

        if json_output:
            print_json(project_data)
        else:
            title = f"Project: {project_data.get('name', '')}"
            content = Text()
            content.append("ID: ", style="bold")
            content.append(f"{project_data.get('id', '')}\n")
            content.append("Name: ", style="bold")
            content.append(f"{project_data.get('name', '')}\n")
            content.append("Path: ", style="bold")
            content.append(f"{project_data.get('path', '')}\n")
            content.append("Sessions: ", style="bold")
            content.append(f"{project_data.get('session_count', 0)}\n")
            content.append("Last Activity: ", style="bold")
            content.append(format_datetime(project_data.get("last_activity")))

            panel = Panel(content, title=title, border_style="green")
            console.print(panel)
    else:
        # Local mode - use services
        project_service = _get_project_service()
        project = project_service.get_project(project_id)

        if project is None:
            print_error(f"Project not found: {project_id}")
            raise typer.Exit(1)

        if json_output:
            print_json(project.model_dump(mode="json"))
        else:
            title = f"Project: {project.name}"
            content = Text()
            content.append("ID: ", style="bold")
            content.append(f"{project.id}\n")
            content.append("Name: ", style="bold")
            content.append(f"{project.name}\n")
            content.append("Path: ", style="bold")
            content.append(f"{project.path}\n")
            content.append("Sessions: ", style="bold")
            content.append(f"{project.session_count}\n")
            content.append("Last Activity: ", style="bold")
            content.append(format_datetime(project.last_activity))

            panel = Panel(content, title=title, border_style="green")
            console.print(panel)


@app.command("stats")
def project_stats(
    project_id: str = typer.Argument(..., help="Project ID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show project statistics."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        try:
            stats_data = client.get_project_stats(project_id)
        except Exception:
            print_error(f"Project not found: {project_id}")
            raise typer.Exit(1) from None

        if json_output:
            print_json(stats_data)
        else:
            title = f"Statistics: {stats_data.get('project_name', '')}"
            content = Text()
            content.append("Project ID: ", style="bold")
            content.append(f"{stats_data.get('project_id', '')}\n")
            content.append("Name: ", style="bold")
            content.append(f"{stats_data.get('project_name', '')}\n")
            content.append("Total Sessions: ", style="bold")
            content.append(f"{stats_data.get('session_count', 0)}\n")
            content.append("Total Messages: ", style="bold")
            content.append(f"{stats_data.get('message_count', 0)}\n")
            content.append("Last Activity: ", style="bold")
            content.append(format_datetime(stats_data.get("last_activity")))

            panel = Panel(content, title=title, border_style="yellow")
            console.print(panel)
    else:
        # Local mode - use services
        project_service = _get_project_service()
        stats = project_service.get_project_stats(project_id)

        if stats is None:
            print_error(f"Project not found: {project_id}")
            raise typer.Exit(1)

        if json_output:
            print_json(stats.model_dump(mode="json"))
        else:
            title = f"Statistics: {stats.project_name}"
            content = Text()
            content.append("Project ID: ", style="bold")
            content.append(f"{stats.project_id}\n")
            content.append("Name: ", style="bold")
            content.append(f"{stats.project_name}\n")
            content.append("Total Sessions: ", style="bold")
            content.append(f"{stats.session_count}\n")
            content.append("Total Messages: ", style="bold")
            content.append(f"{stats.message_count}\n")
            content.append("Last Activity: ", style="bold")
            content.append(format_datetime(stats.last_activity))

            panel = Panel(content, title=title, border_style="yellow")
            console.print(panel)
