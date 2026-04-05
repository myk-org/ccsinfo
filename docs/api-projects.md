# Projects API

The Projects API is the read-only part of `ccsinfo` that groups Claude Code sessions by project. It lets you discover all available projects, inspect one project, list its sessions, see which of those sessions are currently active, and fetch per-project totals without loading every session into the client yourself.

All routes in this page live under `/projects`. The usual workflow is:

1. Call `GET /projects`.
2. Keep the `id` from the project you want.
3. Reuse that same `id` in the detail, sessions, active sessions, and stats endpoints.

> **Tip:** If you are running the built-in API server, it binds to `127.0.0.1:8080` by default. The CLI can also target a remote server with `--server-url` or `CCSINFO_SERVER_URL`.

```27:33:src/ccsinfo/cli/main.py
@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to (use 0.0.0.0 for network access)"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to bind"),
) -> None:
    """Start the API server."""
    uvicorn.run(fastapi_app, host=host, port=port)
```

## At a Glance

| Endpoint | Use it for | Query parameters | Returns |
| --- | --- | --- | --- |
| `GET /projects` | List every known project | None | `Project[]` |
| `GET /projects/{project_id}` | Fetch one project | None | `Project` |
| `GET /projects/{project_id}/sessions` | List sessions for one project | `limit` (`1` to `500`, default `50`) | `SessionSummary[]` |
| `GET /projects/{project_id}/sessions/active` | List currently active sessions for one project | None | `SessionSummary[]` |
| `GET /projects/{project_id}/stats` | Get per-project totals | None | `ProjectStats` |

The server defines those routes exactly like this:

```15:51:src/ccsinfo/server/routers/projects.py
@router.get("", response_model=list[Project])
async def list_projects() -> list[Project]:
    """List all projects."""
    return project_service.list_projects()


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str) -> Project:
    """Get project details."""
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/sessions", response_model=list[SessionSummary])
async def get_project_sessions(
    project_id: str,
    limit: int = Query(50, ge=1, le=500),
) -> list[SessionSummary]:
    """Get sessions for a project."""
    return session_service.list_sessions(project_id=project_id, limit=limit)


@router.get("/{project_id}/sessions/active", response_model=list[SessionSummary])
async def get_project_active_sessions(project_id: str) -> list[SessionSummary]:
    """Get active sessions for a project."""
    return session_service.list_sessions(project_id=project_id, active_only=True)


@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(project_id: str) -> ProjectStats | dict[str, Any]:
    """Get project statistics."""
    stats = project_service.get_project_stats(project_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Project not found")
    return stats
```

## Understanding `project_id`

`project_id` is not a human slug. It is the encoded directory name Claude Code uses under `~/.claude/projects`. The safest pattern is to read it from `GET /projects` and reuse it as-is.

> **Warning:** The decode step is explicitly lossy. Use `path` and `project_path` for display, not as authoritative identifiers.

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

In practice, `/home/user/project` becomes `-home-user-project`. A dotted path such as `/home/user/.config/project` becomes `-home-user--config-project`.

## How the Data Is Assembled

The Projects API is file-backed. It reads Claude Code’s project directories and session JSONL files on demand, then builds project and session summaries from that data. Active session views add a live process check on top of the file data.

```mermaid
flowchart TD
    A[API client] --> B[/projects endpoints]
    B --> C[project_service]
    B --> D[session_service]
    C --> E[~/.claude/projects/<encoded_project_id>/]
    D --> E
    E --> F[session JSONL files]
    B --> G[/projects/{project_id}/sessions/active]
    G --> H[active session detector]
    H --> I[pgrep -f claude and /proc inspection]
```

> **Note:** There is no separate database behind these endpoints. Project and session views come from Claude Code files; active-session status is calculated live.

## Response Objects

All JSON keys use snake_case. Timestamp fields serialize as ISO 8601 strings or `null`.

### `Project`

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Encoded project identifier used in project routes |
| `name` | string | Display name derived from the last segment of the decoded path |
| `path` | string | Decoded project path for display; treat it as approximate |
| `session_count` | integer | Number of session `*.jsonl` files in the project directory |
| `last_activity` | string or `null` | Most recent parsed session timestamp for the project |

### `SessionSummary`

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Session UUID, taken from the session filename |
| `project_path` | string | Decoded project path |
| `project_name` | string | Display name derived from `project_path` |
| `created_at` | string or `null` | First timestamp found in the session |
| `updated_at` | string or `null` | Last timestamp found in the session |
| `message_count` | integer | Count of parsed `user` and `assistant` messages |
| `is_active` | boolean | Whether the session is currently considered active |

### `ProjectStats`

| Field | Type | Description |
| --- | --- | --- |
| `project_id` | string | Encoded project identifier |
| `project_name` | string | Display name for the project |
| `session_count` | integer | Number of sessions in the project |
| `message_count` | integer | Sum of message counts across the project’s sessions |
| `last_activity` | string or `null` | Latest timestamp found across the project’s sessions |

## Endpoint Reference

### `GET /projects`

Use this to discover valid `project_id` values.

Behavior:

- Returns every project as `Project[]`.
- Results are sorted by `last_activity` descending, so the most recently active projects come first.
- There are no query parameters.
- This is the best starting point for clients that need to drill into a specific project.

### `GET /projects/{project_id}`

Use this when you already know the encoded project ID and want one object back.

Behavior:

- Returns a single `Project`.
- The response shape is the same as each item from `GET /projects`.
- It does not include nested sessions or stats.
- If the project does not exist, the server returns `404` with `Project not found`.

### `GET /projects/{project_id}/sessions`

Use this to list a project’s sessions without loading full session detail.

Behavior:

- Returns `SessionSummary[]`.
- Supports a `limit` query parameter with a default of `50`, a minimum of `1`, and a maximum of `500`.
- Results are sorted by `updated_at` descending, so the newest sessions appear first.
- The URL uses the encoded `project_id`, but the response uses decoded display fields such as `project_path` and `project_name`.
- If nothing matches, the endpoint returns an empty list.

> **Note:** `message_count` is based on parsed `user` and `assistant` entries in the session JSONL file, not every raw JSONL record.

### `GET /projects/{project_id}/sessions/active`

Use this when you only want sessions that are currently running.

Behavior:

- Returns `SessionSummary[]` with the same shape as the regular project sessions endpoint.
- There are no query parameters.
- There is no built-in `limit` on this route.
- If no active sessions match the project, the endpoint returns an empty list.

> **Note:** Active status is calculated live, not stored in the session file.

> **Note:** The active-session lookup is cached for 5 seconds, so sessions may take a moment to appear or disappear.

> **Warning:** Active-session detection is best-effort. The implementation looks for running `claude` processes and inspects `/proc`, so results depend on the host environment and permissions.

```252:295:src/ccsinfo/core/parsers/sessions.py
    try:
        # Use pgrep to find claude processes
        result = subprocess.run(
            ["pgrep", "-f", "claude"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            _active_sessions_cache = active_ids
            _active_sessions_cache_time = current_time
            return active_ids

        pids = result.stdout.strip().split("\n")

        # UUID pattern for session IDs
        uuid_pattern = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)

        for pid in pids:
            if not pid:
                continue
            try:
                cmdline_path = Path(f"/proc/{pid}/cmdline")
                if cmdline_path.exists():
                    cmdline = cmdline_path.read_text()
                    # Extract all UUIDs from cmdline
                    active_ids.update(uuid_pattern.findall(cmdline))

                # Also check environment variables
                environ_path = Path(f"/proc/{pid}/environ")
                if environ_path.exists():
                    environ = environ_path.read_text()
                    active_ids.update(uuid_pattern.findall(environ))

                # Check file descriptors for session UUIDs
                fd_dir = Path(f"/proc/{pid}/fd")
                if fd_dir.exists():
                    for fd_link in fd_dir.iterdir():
                        try:
                            target = fd_link.resolve()
                            target_str = str(target)
                            # Look for ~/.claude/tasks/{UUID} or ~/.claude/projects/*/{UUID}.jsonl
                            if ".claude/tasks/" in target_str or ".claude/projects/" in target_str:
                                active_ids.update(uuid_pattern.findall(target_str))
```

### `GET /projects/{project_id}/stats`

Use this when you want per-project totals and recency without aggregating session data in the client.

Behavior:

- Returns a single `ProjectStats` object.
- `session_count` comes from the number of session files in the project.
- `message_count` is the sum of parsed session message counts across that project.
- `last_activity` is the newest timestamp found across the project’s sessions.
- If the project does not exist, the server returns `404` with `Project not found`.

> **Tip:** This is the best project endpoint for dashboard cards, summary panels, and overview pages.

## Missing-Project Behavior

These endpoints do not all behave the same way when a `project_id` does not match anything.

| Endpoint | Missing `project_id` behavior |
| --- | --- |
| `GET /projects/{project_id}` | `404 Project not found` |
| `GET /projects/{project_id}/sessions` | `200 OK` with `[]` |
| `GET /projects/{project_id}/sessions/active` | `200 OK` with `[]` |
| `GET /projects/{project_id}/stats` | `404 Project not found` |

That difference matters if you are building a client. Use the detail or stats endpoints when you want a hard existence check, and use the sessions endpoints when an empty collection is a normal outcome.


## Related Pages

- [Working with Projects](projects-guide.html)
- [API Overview](api-overview.html)
- [Sessions API](api-sessions.html)
- [Project IDs and Lookups](project-ids-and-lookups.html)
- [Stats and Health API](api-stats-and-health.html)