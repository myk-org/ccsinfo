"""Search commands."""

from __future__ import annotations

from typing import Any

import typer
from rich.console import Console

from ccsinfo.cli.state import state
from ccsinfo.core.client import get_client
from ccsinfo.core.services import search_service as _search_service
from ccsinfo.utils.formatters import (
    create_table,
    format_relative_time,
    print_json,
)

app = typer.Typer(help="Search commands")
console = Console()


def _get_search_service() -> Any:
    """Get search_service instance."""
    return _search_service


@app.command("sessions")
def search_sessions(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum results"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Search sessions by ID, project, branch, or directory."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        results_data = client.search_sessions(query=query, limit=limit)

        if json_output:
            print_json(results_data)
        else:
            if not results_data:
                console.print(f"[dim]No sessions found matching '{query}'.[/dim]")
                return

            table = create_table(
                f"Search Results: '{query}'",
                [
                    ("ID", "cyan"),
                    ("Project", "green"),
                    ("Messages", "yellow"),
                    ("Last Activity", "magenta"),
                    ("Status", "blue"),
                ],
            )
            for s in results_data:
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
        search_service = _get_search_service()
        results = search_service.search_sessions(query=query, limit=limit)

        if json_output:
            print_json([r.model_dump(mode="json") for r in results])
        else:
            if not results:
                console.print(f"[dim]No sessions found matching '{query}'.[/dim]")
                return

            table = create_table(
                f"Search Results: '{query}'",
                [
                    ("ID", "cyan"),
                    ("Project", "green"),
                    ("Messages", "yellow"),
                    ("Last Activity", "magenta"),
                    ("Status", "blue"),
                ],
            )
            for s in results:
                table.add_row(
                    s.id[:12],
                    s.project_name,
                    str(s.message_count),
                    format_relative_time(s.updated_at),
                    "[green]Active[/]" if s.is_active else "[dim]Inactive[/]",
                )
            console.print(table)


@app.command("messages")
def search_messages(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum results"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Search message content across all sessions."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        results = client.search_messages(query=query, limit=limit)
    else:
        # Local mode - use services
        search_service = _get_search_service()
        raw_results = search_service.search_messages(query=query, limit=limit)
        # Convert to list of dicts if results are model objects
        results = [r if isinstance(r, dict) else r.model_dump(mode="json") for r in raw_results]

    if json_output:
        print_json(results)
    else:
        if not results:
            console.print(f"[dim]No messages found matching '{query}'.[/dim]")
            return

        table = create_table(
            f"Message Search: '{query}'",
            [
                ("Session", "cyan"),
                ("Type", "green"),
                ("Timestamp", "magenta"),
                ("Snippet", "white"),
            ],
        )
        for r in results:
            # Truncate snippet for display
            snippet = r.get("snippet", "")
            snippet = snippet[:60] + "..." if len(snippet) > 60 else snippet
            snippet = snippet.replace("\n", " ")

            msg_type = r.get("message_type", "unknown")
            type_display = "[green]user[/]" if msg_type == "user" else "[blue]assistant[/]"

            table.add_row(
                r.get("session_id", "")[:12],
                type_display,
                r.get("timestamp", "N/A")[:19] if r.get("timestamp") else "N/A",
                snippet,
            )
        console.print(table)


@app.command("history")
def search_history(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum results"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Search prompt history across all projects."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        results = client.search_history(query=query, limit=limit)
    else:
        # Local mode - use services
        search_service = _get_search_service()
        raw_results = search_service.search_history(query=query, limit=limit)
        # Convert to list of dicts if results are model objects
        results = [r if isinstance(r, dict) else r.model_dump(mode="json") for r in raw_results]

    if json_output:
        print_json(results)
    else:
        if not results:
            console.print(f"[dim]No history entries found matching '{query}'.[/dim]")
            return

        table = create_table(
            f"History Search: '{query}'",
            [
                ("Session", "cyan"),
                ("Timestamp", "magenta"),
                ("Prompt", "white"),
            ],
        )
        for r in results:
            # Truncate prompt for display
            prompt = r.get("prompt", "")
            prompt = prompt[:60] + "..." if len(prompt) > 60 else prompt
            prompt = prompt.replace("\n", " ")

            table.add_row(
                r.get("session_id", "")[:12] if r.get("session_id") else "N/A",
                r.get("timestamp", "N/A")[:19] if r.get("timestamp") else "N/A",
                prompt,
            )
        console.print(table)
