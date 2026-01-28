# ccsinfo

A CLI and REST API for viewing and analyzing Claude Code session data.

## Features

- **List and inspect Claude Code sessions** - Browse all sessions stored in `~/.claude/projects/`
- **View conversation history and tool calls** - Examine messages, assistant responses, and tool invocations
- **Track tasks across sessions** - Monitor pending, in-progress, and completed tasks
- **Search sessions and prompt history** - Find sessions by content or query historical prompts
- **Usage statistics and trends** - Analyze activity patterns with daily and global stats
- **REST API for remote access** - Access session data programmatically via HTTP endpoints
- **Works locally or as client to remote server** - Run standalone or connect to a centralized ccsinfo server

## Installation

```bash
# Install as a CLI tool
uv tool install .
```

### With Chart Support

```bash
# Install with charts extras (for terminal charts)
uv tool install ".[charts]"
```

### Development Installation

```bash
# Clone and install in development mode
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Quick Start

List all sessions:

```bash
$ ccsinfo sessions list
Sessions
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ ID           ┃ Project          ┃ Messages ┃ Last Activity  ┃ Status   ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ a1b2c3d4e5f6 │ my-project       │ 42       │ 5 minutes ago  │ Active   │
│ b2c3d4e5f6a7 │ another-project  │ 18       │ 2 hours ago    │ Inactive │
└──────────────┴──────────────────┴──────────┴────────────────┴──────────┘
```

Show session details:

```bash
$ ccsinfo sessions show a1b2c3d4
╭───────────────────── Session: a1b2c3d4e5f6... ──────────────────────╮
│ ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890                            │
│ Project: my-project                                                  │
│ Path: /home/user/projects/my-project                                 │
│ Created: 2025-01-28 10:30:00                                         │
│ Updated: 2025-01-28 10:35:00                                         │
│ Messages: 42                                                         │
│ Status: Active                                                       │
╰─────────────────────────────────────────────────────────────────────╯
```

View global statistics:

```bash
$ ccsinfo stats global
```

Start the API server:

```bash
$ ccsinfo serve
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8080
```

## CLI Reference

### Sessions

| Command | Description |
|---------|-------------|
| `ccsinfo sessions list` | List all sessions |
| `ccsinfo sessions list --active` | Show only active sessions |
| `ccsinfo sessions list --project <id>` | Filter by project |
| `ccsinfo sessions show <id>` | Show session details |
| `ccsinfo sessions messages <id>` | Show conversation messages |
| `ccsinfo sessions tools <id>` | Show tool calls made in session |
| `ccsinfo sessions active` | Show currently active sessions |

**Examples:**

```bash
# List sessions with JSON output
ccsinfo sessions list --json

# Show messages from a session (partial ID match supported)
ccsinfo sessions messages a1b2c3

# Filter messages by role
ccsinfo sessions messages a1b2c3 --role user

# Show tool calls with details
ccsinfo sessions tools a1b2c3d4
```

### Projects

| Command | Description |
|---------|-------------|
| `ccsinfo projects list` | List all projects |
| `ccsinfo projects show <id>` | Show project details |
| `ccsinfo projects stats <id>` | Show project statistics |

**Examples:**

```bash
# List all projects
ccsinfo projects list

# Show stats for a specific project
ccsinfo projects stats my-project
```

### Tasks

| Command | Description |
|---------|-------------|
| `ccsinfo tasks list` | List all tasks |
| `ccsinfo tasks list -s <session>` | List tasks for a specific session |
| `ccsinfo tasks show <id> -s <session>` | Show task details |
| `ccsinfo tasks pending` | Show pending tasks across all sessions |

**Examples:**

```bash
# List all tasks
ccsinfo tasks list

# Show a specific task from a session
ccsinfo tasks show 5 -s a1b2c3d4

# Show only pending tasks
ccsinfo tasks pending
```

### Statistics

| Command | Description |
|---------|-------------|
| `ccsinfo stats global` | Show global usage statistics |
| `ccsinfo stats daily` | Show daily activity breakdown |
| `ccsinfo stats trends` | Show usage trends over time |

**Examples:**

```bash
# Get global stats in JSON format
ccsinfo stats global --json

# View daily activity
ccsinfo stats daily

# Analyze trends
ccsinfo stats trends
```

### Search

| Command | Description |
|---------|-------------|
| `ccsinfo search sessions <query>` | Search sessions by content |
| `ccsinfo search messages <query>` | Search message content |
| `ccsinfo search history <query>` | Search prompt history |

**Examples:**

```bash
# Search for sessions mentioning "refactor"
ccsinfo search sessions "refactor"

# Search message content
ccsinfo search messages "fix bug"

# Search prompt history
ccsinfo search history "implement feature"
```

### Server

| Command | Description |
|---------|-------------|
| `ccsinfo serve` | Start the REST API server |

**Options:**

```bash
# Start with defaults (127.0.0.1:8080)
ccsinfo serve

# Start on custom host and port for network access
ccsinfo serve --host 0.0.0.0 --port 8080
```

## Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--server-url` | `-s` | Connect to a remote ccsinfo server instead of reading local data |
| `--json` | `-j` | Output results in JSON format (available on most commands) |
| `--version` | `-v` | Show version information |
| `--help` | `-h` | Show help message |

**Examples:**

```bash
# Connect to a remote server
ccsinfo -s http://my-server:8080 sessions list

# Get JSON output
ccsinfo sessions list --json

# Show version
ccsinfo --version
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CCSINFO_SERVER_URL` | Default server URL for client mode | None (local mode) |

**Example:**

```bash
export CCSINFO_SERVER_URL=http://my-server:8080
ccsinfo sessions list  # Uses remote server automatically
```

## Server Mode

Run ccsinfo as a REST API server to provide remote access to session data:

```bash
# Start server with defaults (127.0.0.1:8080)
ccsinfo serve

# Start on all interfaces for network access
ccsinfo serve --host 0.0.0.0 --port 8080
```

The server provides a REST API that mirrors the CLI functionality. Use it to:

- Build dashboards and monitoring tools
- Integrate with other applications
- Access session data from remote machines

## API Reference

### Sessions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions` | GET | List all sessions |
| `/sessions/active` | GET | List active sessions |
| `/sessions/{id}` | GET | Get session details |
| `/sessions/{id}/messages` | GET | Get session messages |
| `/sessions/{id}/tools` | GET | Get session tool calls |
| `/sessions/{id}/tasks` | GET | Get session tasks |
| `/sessions/{id}/progress` | GET | Get session progress |
| `/sessions/{id}/summary` | GET | Get session summary |

**Query Parameters:**

- `GET /sessions`: `project_id`, `active_only`, `limit`
- `GET /sessions/{id}/messages`: `role`, `limit`

### Projects

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/projects` | GET | List all projects |
| `/projects/{id}` | GET | Get project details |
| `/projects/{id}/sessions` | GET | Get project sessions |
| `/projects/{id}/sessions/active` | GET | Get active project sessions |
| `/projects/{id}/stats` | GET | Get project statistics |

### Tasks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tasks` | GET | List all tasks |
| `/tasks/pending` | GET | List pending tasks |
| `/tasks/{id}` | GET | Get task details (requires `session_id` query param) |

**Query Parameters:**

- `GET /tasks`: `session_id`, `status`
- `GET /tasks/{id}`: `session_id` (required)

### Statistics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stats` | GET | Get global statistics |
| `/stats/daily` | GET | Get daily activity |
| `/stats/trends` | GET | Get usage trends |

**Query Parameters:**

- `GET /stats/daily`: `days` (default: 30)

### Search

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search` | GET | Search sessions |
| `/search/history` | GET | Search prompt history |

**Query Parameters:**

- `GET /search`: `q` (required), `limit`
- `GET /search/history`: `q` (required), `limit`

### System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/info` | GET | Server and version information |

### Example API Usage

```bash
# List sessions
curl http://localhost:8080/sessions

# Get session details
curl http://localhost:8080/sessions/a1b2c3d4

# Get messages from a session
curl "http://localhost:8080/sessions/a1b2c3d4/messages?limit=10"

# Search sessions
curl "http://localhost:8080/search?q=refactor"

# Get global stats
curl http://localhost:8080/stats

# Health check
curl http://localhost:8080/health
```

## Moltbot Skill

A Moltbot skill is available for AI assistants to query Claude Code sessions remotely.

**Install via ClawdHub:**

```bash
clawdhub install ccsinfo
```

**Skill page:** https://clawdhub.com/myakove/ccsinfo

The skill allows AI assistants running in Moltbot to:
- Query and analyze Claude Code session data via the ccsinfo REST API
- View conversation history, tool calls, and tasks
- Search sessions and track project statistics
- Monitor active sessions and progress

**Requirements:**
- ccsinfo server running (see Server Mode above)
- `CCSINFO_SERVER_URL` environment variable set to your server

**Example usage:** Ask your Moltbot assistant: *"Show my active Claude Code sessions"* or *"What were the recent tasks in my main project?"*

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/myk-org/ccsinfo.git
cd ccsinfo

# Install development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run tests with tox
tox

# Run tests with pytest directly
uv run pytest

# Run with coverage
uv run pytest --cov=ccsinfo --cov-report=html
```

### Code Quality

```bash
# Run linting
uv run ruff check src/

# Run formatting
uv run ruff format src/

# Run type checking
tox -e typecheck
```

## License

MIT License. See [LICENSE](LICENSE) for details.
