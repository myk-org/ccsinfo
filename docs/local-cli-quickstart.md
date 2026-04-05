## How Local Mode Works

The CLI switches into remote mode only when you pass `--server-url` or set `CCSINFO_SERVER_URL`. Otherwise, it reads local files.

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

> **Note:** If `CCSINFO_SERVER_URL` is set in your shell, unset it before following this walkthrough.

`ccsinfo` resolves the Claude data directory from your current home directory, then reads session files from `~/.claude/projects`.

```8:33:src/ccsinfo/utils/paths.py
def get_claude_base_dir() -> Path:
    """Get the base Claude Code directory (~/.claude)."""
    return Path.home() / ".claude"

def get_projects_dir() -> Path:
    """Get the projects directory (~/.claude/projects)."""
    return get_claude_base_dir() / "projects"

def get_tasks_dir() -> Path:
    """Get the tasks directory (~/.claude/tasks)."""
    return get_claude_base_dir() / "tasks"

def encode_project_path(project_path: str) -> str:
    """Encode a project path to Claude Code's directory name format.

    Claude Code replaces:
    - '/' with '-'
    - '.' with '-'

    Example: '/home/user/project' -> '-home-user-project'
    """
```

That means two practical things:

- Session and stats commands in this page read `~/.claude/projects`.
- Project IDs are encoded directory names, not raw filesystem paths.

```mermaid
flowchart LR
  A["Run `ccsinfo ...`"] --> B{"`--server-url` or `CCSINFO_SERVER_URL` set?"}
  B -- No --> C["Local services"]
  C --> D["Read `~/.claude/projects/<encoded-project>/<session-id>.jsonl`"]
  D --> E["Parse session entries"]
  E --> F["Render Rich tables or JSON"]
  B -- Yes --> G["Remote HTTP client"]
```

> **Tip:** Local mode always reads the current user's `~/.claude`. There is no separate `--claude-dir` flag in this workflow, so make sure you are running as the user whose Claude data you want to inspect.

## List Sessions

Start by browsing what `ccsinfo` can see locally:

```bash
ccsinfo sessions list
```

Useful variations:

```bash
ccsinfo sessions list --limit 100
ccsinfo sessions active
ccsinfo sessions list --json
```

What these do:

- `sessions list` shows up to 50 sessions by default.
- Sessions are sorted by most recent activity first.
- `sessions active` narrows the view to sessions that appear to be attached to a running `claude` process.
- `--json` returns structured data you can inspect or pipe into other tools.

> **Tip:** The table view is great for browsing, but it shortens IDs. Use `ccsinfo sessions list --json` when you need the full `id` for a follow-up command.

If you want to narrow the list to one project, get the full project ID first:

```bash
ccsinfo projects list --json
ccsinfo sessions list --project <project-id>
```

> **Note:** `--project` expects the Claude project ID, which is the encoded directory name under `~/.claude/projects`, not the original filesystem path.

## Inspect One Session

Once you have a full session ID, inspect its summary:

```bash
ccsinfo sessions show <full-session-id>
```

For structured output:

```bash
ccsinfo sessions show <full-session-id> --json
```

The session view includes:

- The full session ID
- Project name and decoded project path
- Created and updated timestamps
- Total message count
- Active/inactive status
- The underlying session file path on disk

> **Warning:** Use the full session ID from `sessions list --json`. In local mode, `ccsinfo` resolves sessions by the exact session filename in `~/.claude/projects/.../<session-id>.jsonl`.

## Inspect Messages

To look inside a session, use the messages command:

```bash
ccsinfo sessions messages <full-session-id>
```

Common filters:

```bash
ccsinfo sessions messages <full-session-id> --role user
ccsinfo sessions messages <full-session-id> --role assistant
ccsinfo sessions messages <full-session-id> --limit 10 --json
```

The table view shows a compact preview for each message:

- Message UUID
- Message type
- Relative timestamp
- A shortened text preview

Use `--json` when you want the full structured message payload instead of a preview.

The test fixture below mirrors the message structure `ccsinfo` parses from session JSONL files:

```26:47:tests/conftest.py
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
```

> **Note:** Message previews are intentionally compact. If a row has little or no visible text, use `--json` to inspect the full content blocks.

> **Tip:** If you want to inspect tool calls for a session, `ccsinfo sessions tools <full-session-id>` is the companion command.

## View Statistics

`ccsinfo` can also summarize your local Claude usage without a server.

Start with the big-picture totals:

```bash
ccsinfo stats global
```

Then drill into recent activity:

```bash
ccsinfo stats daily
ccsinfo stats daily --days 7
ccsinfo stats trends
ccsinfo stats trends --json
```

What each stats command shows:

- `stats global` shows total projects, total sessions, total messages, and total tool calls.
- `stats daily` shows per-day session and message counts for the last 30 days by default.
- `stats trends` shows 7-day and 30-day totals, average session length, most active projects, and most used tools.

> **Note:** `stats daily` groups activity by a session's first timestamp, so a long session is counted on the day it started.

> **Note:** In `stats trends`, the "Most Used Tools" view is session-oriented: a tool is counted by the sessions it appears in, not by every individual invocation.

## A Good Local Workflow

A practical local workflow looks like this:

```bash
ccsinfo sessions list --json
ccsinfo sessions show <full-session-id>
ccsinfo sessions messages <full-session-id> --limit 20
ccsinfo stats trends
```

If that returns no data, check the basics:

- Confirm Claude Code has actually created `~/.claude/projects` for this user.
- Make sure you are not accidentally in remote mode via `CCSINFO_SERVER_URL`.
- Use `--json` whenever you need full session or project IDs instead of the shortened table view.

That is all you need for day-to-day local inspection: list sessions, open one, inspect its messages, and use stats commands to understand recent activity across your Claude history.


## Related Pages

- [Installation](installation.html)
- [Configuration](configuration.html)
- [Working with Sessions](sessions-guide.html)
- [Working with Projects](projects-guide.html)
- [Using Statistics and Trends](statistics-guide.html)