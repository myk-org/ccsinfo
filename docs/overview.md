# Overview

`ccsinfo` is a Python CLI and FastAPI service for exploring Claude Code activity from the data Claude already writes to disk. Instead of manually opening session JSONL files and task JSON files, you get a cleaner view of sessions, projects, tasks, search results, and usage statistics.

It is built for developers and maintainers who want to understand what Claude Code has been doing in a project or on a machine. If you need answers to questions like "What sessions are active?", "What did Claude say in that conversation?", "Which tools were used?", "What tasks are still pending?", or "Which projects were busiest lately?", `ccsinfo` gives you that visibility without forcing you to read raw artifacts by hand.

> **Note:** `ccsinfo` works with Claude Code's existing local artifacts. It does not require a separate export step before it becomes useful.

## What it helps you do

- Browse Claude activity as `sessions`, `projects`, `tasks`, `search`, and `stats` instead of raw files.
- Move from a summary view to the exact messages and tool calls behind it.
- Use the same mental model locally or over HTTP from a remote machine.
- Switch between human-friendly terminal output and JSON output for automation.

## Local or remote, same model

`Local mode:` Run `ccsinfo` on the same machine as Claude Code and it reads the local Claude data directly.

`Remote mode:` Run `ccsinfo serve` where the Claude data lives, then point your CLI at it with `--server-url` or `CCSINFO_SERVER_URL`. The API exposes the same core domains over FastAPI: sessions, projects, tasks, stats, search, plus basic `health` and `info` endpoints.

```mermaid
flowchart LR
    Data["Claude Code data<br/>`~/.claude/projects`<br/>`~/.claude/tasks`"] --> Parsers["Parsers"]
    Parsers --> Services["Services<br/>sessions, projects, tasks, search, stats"]
    Services --> LocalCLI["`ccsinfo` CLI<br/>local mode"]
    Services --> API["FastAPI server"]
    RemoteCLI["`ccsinfo` CLI<br/>with `--server-url`"] --> API
```

The server entrypoint is built into the CLI:

```27:33:src/ccsinfo/cli/main.py
@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to (use 0.0.0.0 for network access)"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to bind"),
) -> None:
    """Start the API server."""
    uvicorn.run(fastapi_app, host=host, port=port)
```

Remote access is configured through the CLI option and environment variable:

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

> **Tip:** Start with local mode when you already have access to the machine that ran Claude Code. Use remote mode when the data lives on another workstation, container, or VM and you want the same workflow without direct filesystem access.

> **Warning:** This repo does not define a built-in authentication or authorization layer for the API. Treat remote mode as a trusted-network tool unless you put it behind your own access controls.

## Where the data comes from

`ccsinfo` reads the same Claude Code directories you would inspect manually, then parses them into higher-level models. The main storage locations are defined directly in the path helpers:

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

From there, `ccsinfo` reads:

- Session transcripts from JSONL files under `~/.claude/projects/...`.
- Prompt history from per-project `.history.jsonl` files.
- Task JSON files from `~/.claude/tasks/<session-id>/`.

The test fixtures in the repo show the kind of local data the parser expects:

```26:62:tests/conftest.py
def sample_session_data() -> list[dict[str, Any]]:
    """Sample session JSONL data."""
    return [
        {
            "type": "user",
            "uuid": "msg-001",
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": "Hello"}],
            },
            "timestamp": "2024-01-15T10:00:00Z",
        },
        {
            "type": "assistant",
            "uuid": "msg-002",
            "parentMessageUuid": "msg-001",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "Hi there!"}],
            },
            "timestamp": "2024-01-15T10:00:01Z",
        },
    ]


@pytest.fixture
def sample_task_data() -> dict[str, Any]:
    """Sample task JSON data."""
    return {
        "id": "1",
        "subject": "Test task",
        "description": "A test task",
        "status": "pending",
        "owner": None,
        "blockedBy": [],
        "blocks": [],
    }
```

> **Note:** The JSONL parser is intentionally tolerant and skips malformed or invalid lines by default, so one bad entry does not make an entire session unreadable.

> **Warning:** Project IDs come from Claude Code's encoded project directory names. They are useful identifiers, but decoded filesystem paths should be treated as approximate when dots and dashes are involved.

## What you can explore

- `sessions` for recent and active sessions, full message streams, and assistant tool calls.
- `projects` for project-level activity, session counts, and last activity.
- `tasks` for Claude task files, including status, owner, blockers, and dependencies.
- `search` for session metadata, message text, and saved prompt history.
- `stats` for totals, daily activity, recent trends, most active projects, most-used tools, and average session length.

In practice, that means you can start broad and then zoom in. Begin with overall activity, identify an interesting project or session, inspect the exact conversation and tool calls behind it, and then jump back out to trends or cross-project search when you need more context.

The search side is broader than just IDs. It looks across session metadata such as slug, working directory, git branch, and project path, and it also searches full message text and prompt history. The analytics side aggregates total sessions, projects, messages, and tool calls, then adds daily views and recent trend summaries.

## Why this matters

The core value of `ccsinfo` is that it makes Claude Code activity explorable at the level humans actually care about. You can work directly from local data when you are on the right machine, or move the same workflow behind a remote service when the data lives somewhere else. Either way, `ccsinfo` turns Claude Code's raw artifacts into something you can query, skim, and understand quickly.


## Related Pages

- [Installation](installation.html)
- [Quickstart: Local CLI Mode](local-cli-quickstart.html)
- [Quickstart: Remote Server Mode](remote-server-quickstart.html)
- [Architecture and Project Structure](architecture-and-project-structure.html)
- [API Overview](api-overview.html)