# Quickstart: Remote Server Mode

`ccsinfo` remote server mode is for the case where your Claude Code data lives on one machine, but you want to inspect it from somewhere else. You start the FastAPI server on the data host with `ccsinfo serve`, then point any `ccsinfo` CLI client at that base URL with `--server-url` or `CCSINFO_SERVER_URL`.

> **Note:** This page assumes the `ccsinfo` command is already installed on the machine that will host the server and on any machine that will act as a client.

## Where the server reads data from

The server does not read data from your current working directory. It reads Claude Code data from the server host's `~/.claude` tree, specifically `~/.claude/projects` and `~/.claude/tasks`:

```8:20:src/ccsinfo/utils/paths.py
def get_claude_base_dir() -> Path:
    """Get the base Claude Code directory (~/.claude)."""
    return Path.home() / ".claude"

def get_projects_dir() -> Path:
    """Get the projects directory (~/.claude/projects)."""
    return get_claude_base_dir() / "projects"

def get_tasks_dir() -> Path:
    """Get the tasks directory (~/.claude/tasks)."""
    return get_claude_base_dir() / "tasks"
```

> **Note:** Start the server on the machine that actually has the Claude Code data you want to browse. Remote mode changes where the client reads from, not where the data is stored.

## Start the server

The `serve` command is intentionally small: it starts Uvicorn with a host and port. The defaults are `127.0.0.1` and `8080`.

```27:33:src/ccsinfo/cli/main.py
@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to (use 0.0.0.0 for network access)"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to bind"),
) -> None:
    """Start the API server."""
    uvicorn.run(fastapi_app, host=host, port=port)
```

If you only need access from the same machine:

```bash
ccsinfo serve
```

If you want other machines to connect to it:

```bash
ccsinfo serve --host 0.0.0.0 --port 8080
```

> **Warning:** The default bind address is `127.0.0.1`, so other machines cannot reach it. For remote access, use `--host 0.0.0.0` or another routable interface.

> **Warning:** The server code in this repo does not configure authentication, authorization, or TLS. Only expose it on a network you trust, or place it behind your own VPN, reverse proxy, or firewall rules.

## What the server exposes

The FastAPI app mounts routers for sessions, projects, tasks, stats, search, and health:

```8:20:src/ccsinfo/server/app.py
app = FastAPI(
    title="ccsinfo",
    description="Claude Code Session Info API",
    version=__version__,
)

# Include routers
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(health.router, tags=["health"])
```

In practice, that gives you a small read-only API with endpoints like:

- `GET /health` and `GET /info`
- `GET /sessions` and `GET /sessions/active`
- `GET /projects`
- `GET /tasks` and `GET /tasks/pending`
- `GET /stats`, `GET /stats/daily`, and `GET /stats/trends`
- `GET /search`, `GET /search/messages`, and `GET /search/history`

> **Note:** In the current codebase, the server routers only expose `GET` handlers. Remote server mode is for reading, listing, and searching Claude Code data, not modifying it.

## Verify the server with health endpoints

The health router defines two endpoints:

```13:27:src/ccsinfo/server/routers/health.py
@router.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}

@router.get("/info")
async def info() -> dict[str, Any]:
    """Server info endpoint."""
    stats = stats_service.get_global_stats()
    return {
        "version": __version__,
        "total_sessions": stats.total_sessions,
        "total_projects": stats.total_projects,
    }
```

Use them as your first smoke test after startup:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/info
```

If you are calling the server from another machine, replace `localhost` with the server hostname or IP address.

What each endpoint tells you:

- `GET /health` confirms that the FastAPI process is up and answering requests.
- `GET /info` confirms that the server can also calculate basic stats, and returns the server `version`, `total_sessions`, and `total_projects`.

> **Tip:** `GET /info` is usually the better quick check. If `/health` works but `/info` shows `0` sessions and `0` projects, the server is up, but it is probably looking at an empty or unexpected `~/.claude` directory on that host.

## Point CLI clients at the server

The CLI has a top-level `--server-url` option, and the same value can be supplied through `CCSINFO_SERVER_URL`:

```43:62:src/ccsinfo/cli/main.py
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
```

Once that URL is set, commands switch from local file access to HTTP requests. For example, `stats global` checks `state.server_url` and uses the HTTP client in remote mode:

```29:38:src/ccsinfo/cli/commands/stats.py
@app.command("global")
def global_stats(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show global statistics."""
    client = get_client(state.server_url)

    if client:
        # Remote mode - use HTTP client
        stats_data = client.get_global_stats()
```

### One-off client calls

Use `--server-url` before the subcommand:

```bash
ccsinfo --server-url http://localhost:8080 stats global
ccsinfo --server-url http://localhost:8080 sessions active
ccsinfo --server-url http://localhost:8080 tasks pending
ccsinfo --server-url http://localhost:8080 search messages "timeout" --json
```

### Persistent shell configuration

If you will run several commands, exporting the URL is more convenient:

```bash
export CCSINFO_SERVER_URL=http://localhost:8080

ccsinfo stats global
ccsinfo sessions active
ccsinfo tasks pending
ccsinfo search messages "timeout" --json
```

> **Tip:** When you want machine-readable output for scripts or pipelines, add `--json`. The CLI commands support both Rich-formatted terminal output and JSON output.

## Request flow

```mermaid
flowchart LR
    A[Client shell] --> B["`ccsinfo` CLI with `--server-url` or `CCSINFO_SERVER_URL`"]
    B --> C["HTTP requests to `ccsinfo serve`"]
    C --> D["FastAPI routers: `/health`, `/info`, `/sessions`, `/projects`, `/tasks`, `/stats`, `/search`"]
    D --> E["ccsinfo services"]
    E --> F["`~/.claude/projects` on the server host"]
    E --> G["`~/.claude/tasks` on the server host"]
```

## Useful first commands

| Goal | CLI or HTTP call | Backing endpoint |
| --- | --- | --- |
| Confirm the API process is alive | `curl http://localhost:8080/health` | `GET /health` |
| Check server version and visible data counts | `curl http://localhost:8080/info` | `GET /info` |
| Get high-level usage totals | `ccsinfo --server-url http://localhost:8080 stats global` | `GET /stats` |
| Show currently active sessions | `ccsinfo --server-url http://localhost:8080 sessions active` | `GET /sessions/active` |
| Show pending tasks | `ccsinfo --server-url http://localhost:8080 tasks pending` | `GET /tasks/pending` |
| Search message content | `ccsinfo --server-url http://localhost:8080 search messages "error" --json` | `GET /search/messages?q=error` |

If you keep those three ideas in mind, remote mode stays simple:

- Start `ccsinfo serve` on the machine with the Claude Code data.
- Verify it with `/health` and `/info`.
- Point your CLI at that base URL with `--server-url` or `CCSINFO_SERVER_URL`.


## Related Pages

- [Installation](installation.html)
- [Configuration](configuration.html)
- [Running the Server](server-operations.html)
- [API Overview](api-overview.html)
- [Stats and Health API](api-stats-and-health.html)