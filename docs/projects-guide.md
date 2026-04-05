# Working with Projects

`ccsinfo` discovers projects automatically from Claude Code data stored under `~/.claude/projects`. A project is not something you register manually. If Claude Code has created a project directory with session files, `ccsinfo` can list it, inspect it, and summarize it.

The test fixtures show the on-disk shape `ccsinfo` expects:

```91:100:tests/conftest.py
# Create projects directory with a sample project
projects_dir = claude_dir / "projects"
project_dir = projects_dir / "-home-user-test-project"
project_dir.mkdir(parents=True)

# Create a session file in the project
session_file = project_dir / "abc-123-def-456.jsonl"
with session_file.open("w") as f:
    for entry in sample_session_data:
        f.write(json.dumps(entry) + "\n")
```

That storage layout drives the rest of the project workflow:
- browse all discovered projects
- inspect one project's metadata
- list that project's sessions to see activity
- summarize the project's overall stats

> **Note:** By default, the CLI reads local Claude Code files directly. If you point it at a running `ccsinfo` server, the same commands use the REST API instead.

## How Project IDs Work

Every project is identified by the encoded directory name Claude Code uses under `~/.claude/projects`. `ccsinfo` uses that encoded name as the project ID in CLI arguments, filters, and API paths.

The encoding logic is defined here:

```23:44:src/ccsinfo/utils/paths.py
def encode_project_path(project_path: str) -> str:
    """Encode a project path to Claude Code's directory name format.

    Claude Code replaces:
    - '/' with '-'
    - '.' with '-'

    Example: '/home/user/project' -> '-home-user-project'
    """
    return project_path.replace("/", "-").replace(".", "-")


def decode_project_path(encoded_path: str) -> str:
    """Decode a Claude Code directory name back to the original path.

    Note: This is lossy - we cannot distinguish between original '-' and encoded '/' or '.'.
    The path returned should be treated as approximate.
    """
    # Handle the pattern where /. becomes --
    result = encoded_path.replace("--", "/.")
    result = result.replace("-", "/")
    return result
```

In practice, a path like `/home/user/project` becomes `-home-user-project`.

> **Warning:** The displayed `path` is reconstructed from the encoded directory name. If the original path contained `-` or `.` characters, the decoded path can be approximate rather than exact.

> **Tip:** `projects list` shortens long IDs in the table view. When you need the exact project ID for a follow-up command, use the full encoded directory name from `~/.claude/projects`.

```mermaid
flowchart LR
  A[~/.claude/projects/<encoded-project>] --> B[Session .jsonl files]
  B --> C[Session parser]
  C --> D[Project service]
  C --> E[Session service]
  D --> F[projects list / projects show / projects stats]
  E --> G[sessions list --project]
  F --> H[CLI output]
  G --> H
  D --> I[/projects and /projects/{id}/stats]
  E --> J[/projects/{id}/sessions]
```

## Browse Projects

Start with the project commands:

```bash
ccsinfo projects list
ccsinfo projects show <project-id>
ccsinfo projects stats <project-id>
```

Use them like this:
- `ccsinfo projects list` gives you the full catalog of discoverable projects.
- `ccsinfo projects show <project-id>` gives you the detail view for one project.
- `ccsinfo projects stats <project-id>` gives you a compact summary of that project's activity.

`projects list` is ordered by most recent activity, so the projects you touched most recently appear first. The detail view is better when you need the full project ID, decoded path, and exact timestamp.

If you prefer HTTP, these are the project endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /projects` | List all projects |
| `GET /projects/{project_id}` | Fetch metadata for one project |
| `GET /projects/{project_id}/sessions` | List sessions for a project |
| `GET /projects/{project_id}/sessions/active` | List only active sessions for a project |
| `GET /projects/{project_id}/stats` | Fetch aggregate stats for a project |

Example requests:

```bash
curl http://127.0.0.1:8080/projects
curl http://127.0.0.1:8080/projects/<project-id>
curl "http://127.0.0.1:8080/projects/<project-id>/sessions?limit=50"
curl http://127.0.0.1:8080/projects/<project-id>/sessions/active
curl http://127.0.0.1:8080/projects/<project-id>/stats
```

The project-session API returns up to 50 sessions by default and accepts values up to 500.

## Inspect Project Metadata

A project's metadata is intentionally small and easy to scan:

| Field | Meaning |
| --- | --- |
| `id` | The encoded project directory name. Use this in CLI commands and API URLs. |
| `name` | A human-friendly name derived from the last segment of the decoded path. |
| `path` | The decoded project path string. Treat it as best-effort. |
| `session_count` | The number of stored session files `ccsinfo` found for that project directory. |
| `last_activity` | The newest timestamp found in that project's session data. |

This is the information you use to answer quick questions such as:
- Which repository or folder does this project correspond to?
- How much stored conversation history does it have?
- When was it last active?

> **Tip:** `projects show` is the most useful command when you are matching an encoded ID back to a real project path.

## Follow Project Activity

Project activity is session-based. On the CLI, that means you move from the `projects` commands to the `sessions` commands:

```bash
ccsinfo sessions list --project <project-id>
ccsinfo sessions list --project <project-id> --active
ccsinfo sessions show <session-id>
```

Use this flow when you want to answer questions like:
- What happened most recently in this project?
- Which sessions are still running?
- Which specific session should I inspect next?

A project-filtered session list gives you:
- the session ID
- the project name
- the message count
- the last activity time
- whether the session appears active

The `--project` filter expects the project ID, not the human-friendly project name.

If you are using the API, the equivalent views are:
- `GET /projects/{project_id}/sessions`
- `GET /projects/{project_id}/sessions/active`

> **Note:** `--active` is a live-process filter. It shows sessions `ccsinfo` currently detects as running, not merely sessions with recent timestamps.

> **Tip:** Think of `projects list` as the catalog, `projects show` as the metadata view, and `sessions list --project <project-id>` as the activity timeline.

## Understand Project Statistics

Use the stats view when you want a compact summary instead of a session-by-session timeline:

```bash
ccsinfo projects stats <project-id>
```

That summary includes:
- `project_id`
- `project_name`
- `session_count`
- `message_count`
- `last_activity`

The core aggregation logic is in `src/ccsinfo/core/services/project_service.py`:

```84:102:src/ccsinfo/core/services/project_service.py
# Calculate detailed stats
total_messages = 0
last_activity = None

for session in get_project_sessions(project_dir):
    total_messages += session.message_count
    session_last = session.last_timestamp
    if session_last:
        session_dt = pendulum.instance(session_last)
        if last_activity is None or session_dt > last_activity:
            last_activity = session_dt

return ProjectStats(
    project_id=project_id,
    project_name=project.name,
    session_count=project.session_count,
    message_count=total_messages,
    last_activity=last_activity,
)
```

This is the practical meaning of each stat:
- `session_count` tells you how many stored session files were found for the project.
- `message_count` tells you how much conversation activity those sessions contain.
- `last_activity` tells you the newest timestamp found across the project's sessions.

> **Note:** In `ccsinfo`, `message_count` is a count of session message entries, not a token count. It reflects conversation volume, not model billing or token usage.

Use project stats when you want a fast answer to questions like:
- Which project has the most conversation history?
- Which project has been active most recently?
- Is this a lightly used project or a busy one?

When you need the story behind the numbers, go back to the filtered session list for that project.

## Use Local Or Server Mode

By default, the CLI reads local Claude Code files. If you set a server URL, the same project commands switch to HTTP calls.

The configuration is wired into the CLI here:

```53:59:src/ccsinfo/cli/main.py
server_url: str | None = typer.Option(
    None,
    "--server-url",
    "-s",
    envvar="CCSINFO_SERVER_URL",
    help="Remote server URL (e.g., http://localhost:8080). If not set, reads local files.",
),
```

Start the built-in API server like this:

```bash
ccsinfo serve
```

By default, it binds to `127.0.0.1:8080`. Once it is running, you can point the CLI at it:

```bash
CCSINFO_SERVER_URL=http://127.0.0.1:8080 ccsinfo projects list
CCSINFO_SERVER_URL=http://127.0.0.1:8080 ccsinfo projects show <project-id>
CCSINFO_SERVER_URL=http://127.0.0.1:8080 ccsinfo sessions list --project <project-id>
```

> **Note:** Local mode and server mode expose the same project concepts. The difference is only where the data is read from.

## Recommended Workflow

1. Run `ccsinfo projects list` to see every discoverable project.
2. Use `ccsinfo projects show <project-id>` to inspect the project path, session count, and last activity.
3. Use `ccsinfo sessions list --project <project-id>` to follow recent work in that project.
4. Add `--active` when you only care about sessions that are currently running.
5. Use `ccsinfo projects stats <project-id>` when you want a concise summary of the project's overall activity.


## Related Pages

- [Project IDs and Lookups](project-ids-and-lookups.html)
- [Working with Sessions](sessions-guide.html)
- [Using Statistics and Trends](statistics-guide.html)
- [Projects API](api-projects.html)
- [Data Model and Storage](data-model-and-storage.html)