"""Statistics commands."""

from __future__ import annotations

from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ccsinfo.cli.state import state
from ccsinfo.core.client import get_client
from ccsinfo.core.services import stats_service as _stats_service
from ccsinfo.utils.formatters import (
    create_table,
    print_json,
)

app = typer.Typer(help="Statistics commands")
console = Console()


def _get_stats_service() -> Any:
    """Get stats_service instance."""
    return _stats_service


@app.command("global")
def global_stats(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show global statistics."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        stats_data = client.get_global_stats()

        if json_output:
            print_json(stats_data)
        else:
            title = "Global Statistics"
            content = Text()
            content.append("Total Projects: ", style="bold")
            content.append(f"{stats_data.get('total_projects', 0)}\n")
            content.append("Total Sessions: ", style="bold")
            content.append(f"{stats_data.get('total_sessions', 0)}\n")
            content.append("Total Messages: ", style="bold")
            content.append(f"{stats_data.get('total_messages', 0)}\n")
            content.append("Total Tool Calls: ", style="bold")
            content.append(f"{stats_data.get('total_tool_calls', 0)}")

            panel = Panel(content, title=title, border_style="green")
            console.print(panel)
    else:
        # Local mode - use services
        stats_service = _get_stats_service()
        stats = stats_service.get_global_stats()

        if json_output:
            print_json(stats.model_dump(mode="json"))
        else:
            title = "Global Statistics"
            content = Text()
            content.append("Total Projects: ", style="bold")
            content.append(f"{stats.total_projects}\n")
            content.append("Total Sessions: ", style="bold")
            content.append(f"{stats.total_sessions}\n")
            content.append("Total Messages: ", style="bold")
            content.append(f"{stats.total_messages}\n")
            content.append("Total Tool Calls: ", style="bold")
            content.append(f"{stats.total_tool_calls}")

            panel = Panel(content, title=title, border_style="green")
            console.print(panel)


@app.command("daily")
def daily_stats(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to show"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show daily statistics."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        stats_data = client.get_daily_stats(days=days)

        if json_output:
            print_json(stats_data)
        else:
            if not stats_data:
                console.print(f"[dim]No activity in the last {days} days.[/dim]")
                return

            table = create_table(
                f"Daily Statistics (Last {days} Days)",
                [
                    ("Date", "cyan"),
                    ("Sessions", "green"),
                    ("Messages", "yellow"),
                ],
            )
            for s in stats_data:
                date_str = str(s.get("date", "Unknown"))
                table.add_row(
                    date_str,
                    str(s.get("session_count", 0)),
                    str(s.get("message_count", 0)),
                )
            console.print(table)
    else:
        # Local mode - use services
        stats_service = _get_stats_service()
        stats = stats_service.get_daily_stats(days=days)

        if json_output:
            print_json([s.model_dump(mode="json") for s in stats])
        else:
            if not stats:
                console.print(f"[dim]No activity in the last {days} days.[/dim]")
                return

            table = create_table(
                f"Daily Statistics (Last {days} Days)",
                [
                    ("Date", "cyan"),
                    ("Sessions", "green"),
                    ("Messages", "yellow"),
                ],
            )
            for s in stats:
                date_str = str(s.date) if s.date else "Unknown"
                table.add_row(
                    date_str,
                    str(s.session_count),
                    str(s.message_count),
                )
            console.print(table)


@app.command("trends")
def trends(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show usage trends."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        trend_data = client.get_trends()
    else:
        # Local mode - use services
        stats_service = _get_stats_service()
        result = stats_service.get_trends()
        # Convert to dict if it's a model object
        trend_data = result if isinstance(result, dict) else result.model_dump(mode="json")

    if json_output:
        print_json(trend_data)
    else:
        # Overview panel
        overview = Text()
        overview.append("Last 7 Days:\n", style="bold underline")
        overview.append("  Sessions: ", style="bold")
        overview.append(f"{trend_data.get('sessions_last_7_days', 0)}\n")
        overview.append("  Messages: ", style="bold")
        overview.append(f"{trend_data.get('messages_last_7_days', 0)}\n")
        overview.append("\nLast 30 Days:\n", style="bold underline")
        overview.append("  Sessions: ", style="bold")
        overview.append(f"{trend_data.get('sessions_last_30_days', 0)}\n")
        overview.append("  Messages: ", style="bold")
        overview.append(f"{trend_data.get('messages_last_30_days', 0)}\n")
        overview.append("\nAverage Session Length: ", style="bold")
        overview.append(f"{trend_data.get('average_session_length', 0)} messages")

        panel = Panel(overview, title="Usage Trends", border_style="blue")
        console.print(panel)

        # Most active projects
        most_active = trend_data.get("most_active_projects", [])
        if most_active:
            table = create_table(
                "Most Active Projects",
                [
                    ("Project", "green"),
                    ("Messages", "yellow"),
                ],
            )
            for project in most_active:
                proj_name = project.get("project", "Unknown")
                # Truncate long project paths
                if len(proj_name) > 50:
                    proj_name = "..." + proj_name[-47:]
                table.add_row(
                    proj_name,
                    str(project.get("message_count", 0)),
                )
            console.print(table)

        # Most used tools
        most_used_tools = trend_data.get("most_used_tools", [])
        if most_used_tools:
            table = create_table(
                "Most Used Tools",
                [
                    ("Tool", "cyan"),
                    ("Count", "yellow"),
                ],
            )
            for tool in most_used_tools:
                table.add_row(
                    tool.get("tool", "Unknown"),
                    str(tool.get("count", 0)),
                )
            console.print(table)
