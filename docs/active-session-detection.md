# Active Session Detection

`ccsinfo` does not store a permanent "active" flag in session files. Instead, it infers activity live by matching each session's UUID against information it can discover from currently running Claude processes.

In practice, that means:

- A session can be **active** even if it has not written a new message recently.
- A session can be **inactive** even if its JSONL file was updated recently, if the Claude process has already exited.
- The answer can lag briefly because `ccsinfo` keeps a short in-memory cache.

> **Note:** `created_at` and `updated_at` come from timestamps inside the session file. `is_active` comes from a separate live process scan.

## Where ccsinfo looks

`ccsinfo` is built around Claude's local data under `~/.claude`. The paths are hard-coded in the project:

```python
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

Those locations matter for active detection because `ccsinfo` uses both of them:

- `~/.claude/projects/` for stored session JSONL files
- `~/.claude/tasks/` as one of the places it inspects when looking at open file descriptors of running Claude processes

## How activity is inferred

Each parsed session asks a live detector whether its UUID is currently active:

```python
def is_active(self) -> bool:
    """Check if this session is currently active."""
    return is_session_active(self.session_id)
```

The detector works like this:

1. Find running processes whose command line contains `claude`.
2. For each matching PID, inspect process metadata.
3. Extract any UUID-looking strings it can find.
4. If one of those UUIDs matches a session ID, mark that session as active.

Here is the core scan from the codebase:

```python
_active_sessions_cache: set[str] | None = None
_active_sessions_cache_time: float = 0.0
_CACHE_TTL_SECONDS: float = 5.0


def _get_active_session_ids() -> set[str]:
    """Get all active session IDs from running Claude processes.

    This function caches the result for a short time to avoid
    repeated expensive pgrep calls.
    """
    global _active_sessions_cache, _active_sessions_cache_time

    current_time = time.monotonic()

    # Return cached result if still valid
    if _active_sessions_cache is not None and (current_time - _active_sessions_cache_time) < _CACHE_TTL_SECONDS:
        return _active_sessions_cache

    active_ids: set[str] = set()

    try:
        # Use pgrep to find claude processes
        result = subprocess.run(
            ["pgrep", "-f", "claude"],
            capture_output=True,
            text=True,
            timeout=5,
        )
```

And this is how UUIDs are gathered from each PID:

```python
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
                        except (OSError, PermissionError):
                            continue
            except (PermissionError, FileNotFoundError, OSError):
                continue
```

A few important details fall out of this design:

- `ccsinfo` is not guessing based on file timestamps alone.
- The match key is the **session UUID**, not the project name.
- The first process filter is broad (`pgrep -f claude`), but a session is only marked active after a UUID match is found.

## Data flow

```mermaid
flowchart TD
    A[User runs a session command or API request] --> B[ccsinfo parses session JSONL files]
    B --> C[Session.is_active()]
    C --> D{Active ID cache younger than 5s?}
    D -- Yes --> E[Reuse cached set of session UUIDs]
    D -- No --> F[Run pgrep -f claude]
    F --> G[Inspect /proc/<pid>/cmdline]
    G --> H[Inspect /proc/<pid>/environ]
    H --> I[Inspect resolved /proc/<pid>/fd targets]
    I --> J[Extract UUIDs]
    J --> K[Store UUID set in cache]
    E --> L[Compare session UUID to active UUID set]
    K --> L
    L --> M[Expose is_active in CLI and API results]
```

## The short-lived cache

The active-session scan is cached in memory for **5 seconds**. This is one shared cache of active session IDs, not a separate cache per session.

That helps in two ways:

- Listing many sessions does not run `pgrep` once per session.
- Repeated CLI or API calls within a few seconds stay fast.

It also creates a few user-visible behaviors:

- A newly started or newly ended Claude session can take up to 5 seconds to show the new status.
- If a probe returns no active IDs, that empty result is also cached for up to 5 seconds.
- The `pgrep` lookup itself has a 5-second timeout, so refreshes are bounded instead of hanging indefinitely.

> **Tip:** If a session just started or stopped, wait a few seconds and try again before assuming the status is wrong.

> **Note:** There is no user-facing setting in the current codebase to tune the cache TTL or change the process-matching pattern. Both are hard-coded.

## Local mode vs server mode

The CLI can work either against local files or against a remote `ccsinfo` server. The switch is `--server-url` or `CCSINFO_SERVER_URL`:

```python
server_url: str | None = typer.Option(
    None,
    "--server-url",
    "-s",
    envvar="CCSINFO_SERVER_URL",
    help="Remote server URL (e.g., http://localhost:8080). If not set, reads local files.",
)
```

This matters for active detection:

- In local mode, `ccsinfo` checks the machine where you run the CLI.
- In server mode, the server performs the process scan and returns the result.

> **Warning:** If you use `--server-url`, the `is_active` value describes the server host, not your local machine.

## Where you see the result

The active flag is surfaced in both the CLI and the API.

### CLI

Use either of these commands:

```bash
ccsinfo sessions active
ccsinfo sessions list --active
```

If you are talking to a server instead of local files:

```bash
ccsinfo --server-url http://localhost:8080 sessions active
```

### API

These routes expose active-session results:

- `GET /sessions/active`
- `GET /sessions?active_only=true`
- `GET /projects/{project_id}/sessions/active`

## Platform-specific caveats

`ccsinfo` currently depends on two platform behaviors:

- `pgrep -f claude` must exist
- Linux-style `/proc/<pid>` inspection must be available

That means support is best on Linux.

> **Warning:** On systems without a usable `/proc` filesystem, active-session detection can fall back to reporting no active sessions.

### Linux

Linux is the best fit for the current implementation. `pgrep` and `/proc/<pid>` are both expected, so `ccsinfo` can inspect command lines, environments, and open file descriptors.

### macOS

macOS usually has `pgrep`, but it does not provide Linux-style `/proc/<pid>` files. In practice, that means `ccsinfo` may find Claude PIDs but still fail to extract session UUIDs, so active sessions can appear inactive.

### Windows

The current detector expects `pgrep` and `/proc`, so Windows does not match the implementation well. If the process scan cannot run, `ccsinfo` quietly returns an empty active-session set for that check.

### Containers and restricted environments

Even on Linux, process visibility can be limited by PID namespaces, container boundaries, or permissions. `ccsinfo` skips unreadable PIDs and file descriptors, so the result can be partial rather than all-or-nothing.

> **Note:** Detection failures are handled quietly in the current code. If `pgrep` is missing, times out, or `/proc` entries cannot be read, `ccsinfo` does not raise a user-facing error for session listings; it simply reports no matches for that probe.

## Troubleshooting

If a session you expect to be active shows up as inactive, check these first:

1. Wait at least 5 seconds and run the command again.
2. Make sure you are checking the same machine that is running Claude.
3. If you are using `--server-url` or `CCSINFO_SERVER_URL`, remember the server host is doing the detection.
4. On macOS, Windows, or locked-down containers, the process scan may not be able to read the data it needs.
5. If Claude's running process does not expose the session UUID in its command line, environment, or relevant open file paths, `ccsinfo` has nothing reliable to match.

> **Tip:** If you want the most reliable results today, run `ccsinfo` locally on a Linux machine that is also running Claude.


## Related Pages

- [Working with Sessions](sessions-guide.html)
- [Sessions API](api-sessions.html)
- [Quickstart: Local CLI Mode](local-cli-quickstart.html)
- [Running the Server](server-operations.html)
- [Troubleshooting](troubleshooting.html)