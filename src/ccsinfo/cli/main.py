"""Main CLI application for ccsinfo."""

from __future__ import annotations

import typer
import uvicorn

from ccsinfo import __version__
from ccsinfo.cli.commands import projects, search, sessions, stats, tasks
from ccsinfo.cli.state import state
from ccsinfo.server.app import app as fastapi_app

app = typer.Typer(
    name="ccsinfo",
    help="Claude Code Session Info CLI",
    no_args_is_help=True,
)

# Add command groups
app.add_typer(sessions.app, name="sessions", help="Session management")
app.add_typer(projects.app, name="projects", help="Project management")
app.add_typer(tasks.app, name="tasks", help="Task management")
app.add_typer(stats.app, name="stats", help="Statistics")
app.add_typer(search.app, name="search", help="Search")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to (use 0.0.0.0 for network access)"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to bind"),
) -> None:
    """Start the API server."""
    uvicorn.run(fastapi_app, host=host, port=port)


def version_callback(value: bool) -> None:
    """Handle --version flag."""
    if value:
        typer.echo(f"ccsinfo v{__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    _version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version information.",
        callback=version_callback,
        is_eager=True,
    ),
    server_url: str | None = typer.Option(
        None,
        "--server-url",
        "-s",
        envvar="CCSINFO_SERVER_URL",
        help="Remote server URL (e.g., http://localhost:8080). If not set, reads local files.",
    ),
) -> None:
    """Claude Code Session Info CLI."""
    state.server_url = server_url


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
