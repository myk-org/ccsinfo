"""Session management commands."""

from __future__ import annotations

from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel

from ccsinfo.cli.state import state
from ccsinfo.core.client import get_client
from ccsinfo.core.services import session_service as _session_service
from ccsinfo.utils.formatters import (
    create_table,
    format_datetime,
    format_relative_time,
    print_error,
    print_json,
)

app = typer.Typer(help="Session management commands")
console = Console()


def _get_session_service() -> Any:
    """Get session_service instance."""
    return _session_service


@app.command("list")
def list_sessions(
    project: str | None = typer.Option(None, "--project", "-p", help="Filter by project ID"),
    active: bool = typer.Option(False, "--active", "-a", help="Show only active sessions"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum sessions to show"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """List all sessions."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        sessions_data = client.list_sessions(project_id=project, active_only=active, limit=limit)
        if json_output:
            print_json(sessions_data)
        else:
            if not sessions_data:
                console.print("[dim]No sessions found.[/dim]")
                return

            table = create_table(
                "Sessions",
                [
                    ("ID", "cyan"),
                    ("Project", "green"),
                    ("Messages", "yellow"),
                    ("Last Activity", "magenta"),
                    ("Status", "blue"),
                ],
            )
            for s in sessions_data:
                table.add_row(
                    s["id"][:12],
                    s.get("project_name", ""),
                    str(s.get("message_count", 0)),
                    format_relative_time(s.get("updated_at")),
                    "[green]Active[/]" if s.get("is_active") else "[dim]Inactive[/]",
                )
            console.print(table)
    else:
        # Local mode - use services
        session_service = _get_session_service()
        sessions = session_service.list_sessions(project_id=project, active_only=active, limit=limit)

        if json_output:
            print_json([s.model_dump(mode="json") for s in sessions])
        else:
            if not sessions:
                console.print("[dim]No sessions found.[/dim]")
                return

            table = create_table(
                "Sessions",
                [
                    ("ID", "cyan"),
                    ("Project", "green"),
                    ("Messages", "yellow"),
                    ("Last Activity", "magenta"),
                    ("Status", "blue"),
                ],
            )
            for s in sessions:
                table.add_row(
                    s.id[:12],
                    s.project_name,
                    str(s.message_count),
                    format_relative_time(s.updated_at),
                    "[green]Active[/]" if s.is_active else "[dim]Inactive[/]",
                )
            console.print(table)


@app.command("show")
def show_session(
    session_id: str = typer.Argument(..., help="Session ID (can be partial)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show session details."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        try:
            session_data = client.get_session(session_id)
        except Exception:
            print_error(f"Session not found: {session_id}")
            raise typer.Exit(1) from None

        if json_output:
            print_json(session_data)
        else:
            title = f"Session: {session_data['id'][:12]}..."
            status = "[green]Active[/green]" if session_data.get("is_active") else "[dim]Inactive[/dim]"
            file_line = f"\n[bold]File:[/bold] {session_data.get('file_path')}" if session_data.get("file_path") else ""

            content = (
                f"[bold]ID:[/bold] {session_data['id']}\n"
                f"[bold]Project:[/bold] {session_data.get('project_name', '')}\n"
                f"[bold]Path:[/bold] {session_data.get('project_path', '')}\n"
                f"[bold]Created:[/bold] {format_datetime(session_data.get('created_at'))}\n"
                f"[bold]Updated:[/bold] {format_datetime(session_data.get('updated_at'))}\n"
                f"[bold]Messages:[/bold] {session_data.get('message_count', 0)}\n"
                f"[bold]Status:[/bold] {status}"
                f"{file_line}"
            )

            panel = Panel(content, title=title, border_style="cyan")
            console.print(panel)
    else:
        # Local mode - use services
        session_service = _get_session_service()
        session = session_service.get_session(session_id)

        if session is None:
            print_error(f"Session not found: {session_id}")
            raise typer.Exit(1)

        if json_output:
            print_json(session.model_dump(mode="json"))
        else:
            # Create a detailed view using markup for proper rendering
            title = f"Session: {session.id[:12]}..."
            status = "[green]Active[/green]" if session.is_active else "[dim]Inactive[/dim]"
            file_line = f"\n[bold]File:[/bold] {session.file_path}" if session.file_path else ""

            content = (
                f"[bold]ID:[/bold] {session.id}\n"
                f"[bold]Project:[/bold] {session.project_name}\n"
                f"[bold]Path:[/bold] {session.project_path}\n"
                f"[bold]Created:[/bold] {format_datetime(session.created_at)}\n"
                f"[bold]Updated:[/bold] {format_datetime(session.updated_at)}\n"
                f"[bold]Messages:[/bold] {session.message_count}\n"
                f"[bold]Status:[/bold] {status}"
                f"{file_line}"
            )

            panel = Panel(content, title=title, border_style="cyan")
            console.print(panel)


@app.command("messages")
def session_messages(
    session_id: str = typer.Argument(..., help="Session ID"),
    role: str | None = typer.Option(None, "--role", "-r", help="Filter by role (user/assistant)"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum messages"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show messages from a session."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        messages_data = client.get_session_messages(session_id=session_id, role=role, limit=limit)

        if not messages_data:
            try:
                client.get_session(session_id)
            except Exception:
                print_error(f"Session not found: {session_id}")
                raise typer.Exit(1) from None
            console.print("[dim]No messages found.[/dim]")
            return

        if json_output:
            print_json(messages_data)
        else:
            table = create_table(
                "Messages",
                [
                    ("UUID", "cyan"),
                    ("Type", "green"),
                    ("Time", "magenta"),
                    ("Content Preview", "white"),
                ],
            )
            for msg in messages_data:
                # Truncate content for display
                content = msg.get("text_content", "")
                content_preview = content[:60] + "..." if len(content) > 60 else content
                content_preview = content_preview.replace("\n", " ")

                msg_type = msg.get("type", "")
                role_style = "[green]user[/]" if msg_type == "user" else "[blue]assistant[/]"

                table.add_row(
                    msg.get("uuid", "")[:8] if msg.get("uuid") else "N/A",
                    role_style,
                    format_relative_time(msg.get("timestamp")),
                    content_preview or "[dim]<tool calls only>[/dim]",
                )
            console.print(table)
    else:
        # Local mode - use services
        session_service = _get_session_service()
        messages = session_service.get_session_messages(session_id=session_id, role=role, limit=limit)

        if not messages:
            session = session_service.get_session(session_id)
            if session is None:
                print_error(f"Session not found: {session_id}")
                raise typer.Exit(1)
            console.print("[dim]No messages found.[/dim]")
            return

        if json_output:
            print_json([m.model_dump(mode="json") for m in messages])
        else:
            table = create_table(
                "Messages",
                [
                    ("UUID", "cyan"),
                    ("Type", "green"),
                    ("Time", "magenta"),
                    ("Content Preview", "white"),
                ],
            )
            for msg in messages:
                # Truncate content for display
                content = msg.text_content
                content_preview = content[:60] + "..." if len(content) > 60 else content
                content_preview = content_preview.replace("\n", " ")

                role_style = "[green]user[/]" if msg.type == "user" else "[blue]assistant[/]"

                table.add_row(
                    msg.uuid[:8] if msg.uuid else "N/A",
                    role_style,
                    format_relative_time(msg.timestamp),
                    content_preview or "[dim]<tool calls only>[/dim]",
                )
            console.print(table)


@app.command("tools")
def session_tools(
    session_id: str = typer.Argument(..., help="Session ID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show tool calls from a session."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        tools = client.get_session_tools(session_id)

        if not tools:
            try:
                client.get_session(session_id)
            except Exception:
                print_error(f"Session not found: {session_id}")
                raise typer.Exit(1) from None
            console.print("[dim]No tool calls found.[/dim]")
            return

        if json_output:
            print_json(tools)
        else:
            table = create_table(
                "Tool Calls",
                [
                    ("ID", "cyan"),
                    ("Tool Name", "green"),
                    ("Input Preview", "white"),
                ],
            )
            for tool in tools:
                # Format input preview
                input_str = str(tool.get("input", {}))
                input_preview = input_str[:80] + "..." if len(input_str) > 80 else input_str

                table.add_row(
                    tool.get("id", "")[:12],
                    tool.get("name", ""),
                    input_preview,
                )
            console.print(table)
    else:
        # Local mode - use services
        session_service = _get_session_service()
        tools = session_service.get_session_tools(session_id)

        if not tools:
            session = session_service.get_session(session_id)
            if session is None:
                print_error(f"Session not found: {session_id}")
                raise typer.Exit(1)
            console.print("[dim]No tool calls found.[/dim]")
            return

        if json_output:
            print_json(tools)
        else:
            table = create_table(
                "Tool Calls",
                [
                    ("ID", "cyan"),
                    ("Tool Name", "green"),
                    ("Input Preview", "white"),
                ],
            )
            for tool in tools:
                # Format input preview
                input_str = str(tool.get("input", {}))
                input_preview = input_str[:80] + "..." if len(input_str) > 80 else input_str

                table.add_row(
                    tool.get("id", "")[:12],
                    tool.get("name", ""),
                    input_preview,
                )
            console.print(table)


@app.command("active")
def active_sessions(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show currently active sessions."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        sessions_data = client.get_active_sessions()

        if json_output:
            print_json(sessions_data)
        else:
            if not sessions_data:
                console.print("[dim]No active sessions.[/dim]")
                return

            table = create_table(
                "Active Sessions",
                [
                    ("ID", "cyan"),
                    ("Project", "green"),
                    ("Messages", "yellow"),
                    ("Last Activity", "magenta"),
                ],
            )
            for s in sessions_data:
                table.add_row(
                    s["id"][:12],
                    s.get("project_name", ""),
                    str(s.get("message_count", 0)),
                    format_relative_time(s.get("updated_at")),
                )
            console.print(table)
    else:
        # Local mode - use services
        session_service = _get_session_service()
        sessions = session_service.get_active_sessions()

        if json_output:
            print_json([s.model_dump(mode="json") for s in sessions])
        else:
            if not sessions:
                console.print("[dim]No active sessions.[/dim]")
                return

            table = create_table(
                "Active Sessions",
                [
                    ("ID", "cyan"),
                    ("Project", "green"),
                    ("Messages", "yellow"),
                    ("Last Activity", "magenta"),
                ],
            )
            for s in sessions:
                table.add_row(
                    s.id[:12],
                    s.project_name,
                    str(s.message_count),
                    format_relative_time(s.updated_at),
                )
            console.print(table)
