# Stats and Health API

`ccsinfo` exposes five read-only endpoints for analytics and server status. Use them when you want a quick snapshot of all Claude Code activity, a daily activity series, ranked trend data, or a simple signal that the server is up.

| Endpoint | What it is for |
| --- | --- |
| `GET /stats` | Global totals across all parsed sessions and projects |
| `GET /stats/daily` | Day-by-day activity for the last `N` days |
| `GET /stats/trends` | Trend summary, top projects, top tools, and average session length |
| `GET /health` | Simple liveness check |
| `GET /info` | Lightweight server metadata and top-level counts |

The routes are mounted directly on the FastAPI app, with stats under `/stats` and health/info at the root:

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

The project configuration shows the API stack is built around FastAPI, Uvicorn, and `httpx`:

```52:60:pyproject.toml
dependencies = [
  "typer>=0.9.0",
  "rich>=13.0.0",
  "orjson>=3.9.0",
  "pydantic>=2.0.0",
  "pendulum>=3.0.0",
  "fastapi>=0.109.0",
  "uvicorn[standard]>=0.27.0",
  "httpx>=0.27.0",
]
```

> **Warning:** The FastAPI app in this repository does not add authentication, authorization, or custom middleware around these routes. If you expose the server beyond localhost, put it behind your own access controls.

## Where the stats come from

All stats are calculated from Claude Code session files under `~/.claude/projects`. Each session is stored as JSONL, with one event per line. The test suite includes a minimal example that matches the format the parser expects:

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

A “message” is not a token count or a duration estimate. It is a session entry whose `type` is `user` or `assistant`, and a “tool call” is an assistant content block whose `type` is `tool_use`:

```116:140:src/ccsinfo/core/parsers/sessions.py
@property
def message_count(self) -> int:
    """Count of message entries (user + assistant)."""
    return sum(1 for e in self.entries if e.type in ("user", "assistant"))

@property
def tool_use_count(self) -> int:
    """Count of tool use entries."""
    count = 0
    for entry in self.entries:
        if entry.type == "assistant" and entry.message:
            content = entry.message.content
            if isinstance(content, list):
                count += sum(1 for c in content if isinstance(c, MessageContent) and c.type == "tool_use")
    return count
```

```mermaid
flowchart LR
  A[Client request] --> B[FastAPI router]
  B --> C[StatsService]
  C --> D[get_all_sessions()]
  D --> E[~/.claude/projects]
  E --> F[Session *.jsonl files]
  F --> G[Parsed Session objects]
  G --> C
  C --> H[JSON response]

  I[GET /health] --> J[Health router]
  J --> K[status healthy]
```

## `GET /stats`

Use `GET /stats` when you want top-level counters for dashboards, sanity checks, or a quick “does this server see my data?” overview.

The global stats service totals all parsed sessions, tracks the unique projects they belong to, and sums both message counts and tool-use counts:

```20:46:src/ccsinfo/core/services/stats_service.py
def get_global_stats(self) -> GlobalStats:
    """Get global usage statistics across all sessions and projects.

    Returns:
        GlobalStats object with totals.
    """
    total_sessions = 0
    total_projects = 0
    total_messages = 0
    total_tool_calls = 0

    project_ids = set()

    for project_path, session in get_all_sessions():
        total_sessions += 1
        project_ids.add(project_path)
        total_messages += session.message_count
        total_tool_calls += session.tool_use_count

    total_projects = len(project_ids)

    return GlobalStats(
        total_sessions=total_sessions,
        total_projects=total_projects,
        total_messages=total_messages,
        total_tool_calls=total_tool_calls,
    )
```

Response fields:

| Field | Meaning |
| --- | --- |
| `total_sessions` | Total number of parsed session files |
| `total_projects` | Number of unique projects that contributed sessions |
| `total_messages` | Sum of all `user` and `assistant` session entries |
| `total_tool_calls` | Sum of all assistant `tool_use` content blocks |

> **Tip:** If you just need high-level counters, call `/stats`. If you only need version plus project/session counts, `/info` is lighter.

## `GET /stats/daily`

Use `GET /stats/daily` for activity charts and recent daily rollups.

This endpoint accepts one query parameter:

| Parameter | Default | Limits | Meaning |
| --- | --- | --- | --- |
| `days` | `30` | `1` to `365` | How many trailing days to include |

The service groups sessions by the session’s first timestamp, not by every message timestamp, then sorts the results by date:

```57:90:src/ccsinfo/core/services/stats_service.py
now = pendulum.now()
cutoff = now.subtract(days=days)

# Aggregate by date
daily_data: dict[str, dict[str, int]] = defaultdict(lambda: {"session_count": 0, "message_count": 0})

for _project_path, session in get_all_sessions():
    # Use the session's first timestamp as the activity date
    ts = session.first_timestamp
    if ts is None:
        continue

    session_dt = pendulum.instance(ts)
    if session_dt < cutoff:
        continue

    date_key = session_dt.format("YYYY-MM-DD")
    daily_data[date_key]["session_count"] += 1
    daily_data[date_key]["message_count"] += session.message_count

# Convert to DailyStats objects
results: list[DailyStats] = []
for date_str, data in sorted(daily_data.items()):
    parsed_dt = pendulum.parse(date_str)
    date = parsed_dt.date() if parsed_dt else None
    results.append(
        DailyStats(
            date=date,
            session_count=data["session_count"],
            message_count=data["message_count"],
        )
    )

return results
```

Each item in the response includes:

| Field | Meaning |
| --- | --- |
| `date` | The day bucket for the session start date |
| `session_count` | How many sessions started on that day |
| `message_count` | Total messages from those sessions |

Important behavior to know:

- Only days with activity are returned.
- Results are ordered from oldest day to newest day.
- Sessions without a timestamp are skipped.
- All messages from a session are assigned to the day of that session’s first timestamp.

> **Warning:** `/stats/daily` is a session-start view, not a true per-calendar-day message distribution. A long session that crosses midnight is still counted on its start date.

> **Tip:** If you need a continuous chart, fill in missing dates on the client side. The API does not add zero-value days.

## `GET /stats/trends`

Use `GET /stats/trends` when you want a compact analytics summary rather than raw totals.

The trend service computes recent 7-day and 30-day counts, ranks projects by message volume, ranks tools by usage, and calculates an average session length:

```119:163:src/ccsinfo/core/services/stats_service.py
for project_path, session in get_all_sessions():
    total_sessions += 1
    total_messages += session.message_count
    project_activity[project_path] += session.message_count

    # Collect tool usage
    for tool in session.get_unique_tools_used():
        tool_usage[tool] += 1

    ts = session.first_timestamp
    if ts is not None:
        session_dt = pendulum.instance(ts)
        if session_dt >= cutoff_30:
            sessions_30 += 1
            messages_30 += session.message_count
            if session_dt >= cutoff_7:
                sessions_7 += 1
                messages_7 += session.message_count

# Calculate most active projects
most_active = sorted(
    project_activity.items(),
    key=lambda x: x[1],
    reverse=True,
)[:5]

# Calculate most used tools
most_used_tools = sorted(
    tool_usage.items(),
    key=lambda x: x[1],
    reverse=True,
)[:10]

# Average session length
avg_length = total_messages / total_sessions if total_sessions > 0 else 0

return {
    "sessions_last_7_days": sessions_7,
    "sessions_last_30_days": sessions_30,
    "messages_last_7_days": messages_7,
    "messages_last_30_days": messages_30,
    "most_active_projects": [{"project": p, "message_count": c} for p, c in most_active],
    "most_used_tools": [{"tool": t, "count": c} for t, c in most_used_tools],
    "average_session_length": round(avg_length, 2),
}
```

Response fields:

| Field | Meaning |
| --- | --- |
| `sessions_last_7_days` | Sessions whose first timestamp is within the last 7 days |
| `sessions_last_30_days` | Sessions whose first timestamp is within the last 30 days |
| `messages_last_7_days` | Total messages from those 7-day sessions |
| `messages_last_30_days` | Total messages from those 30-day sessions |
| `most_active_projects` | Top 5 project paths ranked by total message count |
| `most_used_tools` | Top 10 tools ranked by usage count |
| `average_session_length` | Average number of messages per session, rounded to 2 decimals |

Tool usage is intentionally based on unique tools per session, not every repeated call inside the same session:

```205:215:src/ccsinfo/core/parsers/sessions.py
def get_unique_tools_used(self) -> set[str]:
    """Get the set of unique tool names used in the session."""
    tools: set[str] = set()
    for entry in self.entries:
        if entry.type == "assistant" and entry.message:
            content = entry.message.content
            if isinstance(content, list):
                for c in content:
                    if isinstance(c, MessageContent) and c.type == "tool_use" and c.name:
                        tools.add(c.name)
    return tools
```

That means:

- `most_active_projects` is based on message volume, not session count.
- `project` values are project paths, not opaque project IDs.
- `most_used_tools` counts whether a tool appeared in a session at least once.
- `average_session_length` is a message average, not a time duration.

> **Warning:** A session that uses the same tool 20 times still contributes `1` to that tool’s trend count.

> **Warning:** `average_session_length` does not measure elapsed time. It is `total_messages / total_sessions`.

> **Note:** The 7-day and 30-day windows use each session’s first timestamp. Sessions without timestamps are excluded from those windowed counts but still affect all-time totals like `average_session_length`.

## `GET /health`

Use `GET /health` for a simple liveness probe.

## `GET /info`

Use `GET /info` for a lightweight status summary that includes the server version plus total session and project counts.

Both endpoints are defined in the same router:

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

Behavior summary:

| Endpoint | Response |
| --- | --- |
| `GET /health` | Always returns `{"status": "healthy"}` |
| `GET /info` | Returns `version`, `total_sessions`, and `total_projects` |

> **Note:** `/health` is a liveness check only. It does not verify that `~/.claude/projects` exists, that session files are readable, or that any stats can actually be computed.

> **Tip:** If you want a small “is the service up and does it see data?” check, prefer `/info`. If you need message and tool totals too, call `/stats` instead.


## Related Pages

- [Using Statistics and Trends](statistics-guide.html)
- [API Overview](api-overview.html)
- [Running the Server](server-operations.html)
- [Quickstart: Remote Server Mode](remote-server-quickstart.html)
- [JSON Output and Automation](json-output-and-automation.html)