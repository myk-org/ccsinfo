---
name: ccsinfo
description: Query and analyze Claude Code session data from a remote server
required_binaries:
  - ccsinfo
required_env:
  - CCSINFO_SERVER_URL
install_script: scripts/install.sh
---

# ccsinfo - Claude Code Session Info

You have access to the `ccsinfo` CLI tool for querying Claude Code session data from a remote server.

## Important

- Always use `--json` flag for machine-readable output
- The tool connects to a remote ccsinfo server via `CCSINFO_SERVER_URL`
- Use partial session IDs when possible (the tool supports prefix matching)

## Available Commands

### Sessions

List sessions:
```bash
ccsinfo sessions list --json
ccsinfo sessions list --active --json
ccsinfo sessions list --project <project_id> --json
ccsinfo sessions list --limit <n> --json
```

Show session details:
```bash
ccsinfo sessions show <session_id> --json
```

View conversation messages:
```bash
ccsinfo sessions messages <session_id> --json
ccsinfo sessions messages <session_id> --role user --json
ccsinfo sessions messages <session_id> --limit <n> --json
```

View tool calls:
```bash
ccsinfo sessions tools <session_id> --json
```

List active sessions:
```bash
ccsinfo sessions active --json
```

### Projects

```bash
ccsinfo projects list --json
ccsinfo projects show <project_id> --json
ccsinfo projects stats <project_id> --json
```

### Tasks

```bash
ccsinfo tasks list --json
ccsinfo tasks list --session <session_id> --json
ccsinfo tasks list --status pending --json
ccsinfo tasks show <task_id> --session <session_id> --json
ccsinfo tasks pending --json
```

### Statistics

```bash
ccsinfo stats global --json
ccsinfo stats daily --json
ccsinfo stats daily --days <n> --json
ccsinfo stats trends --json
```

### Search

```bash
ccsinfo search sessions "<query>" --json
ccsinfo search messages "<query>" --json
ccsinfo search history "<query>" --json
ccsinfo search sessions "<query>" --limit <n> --json
```

## Workflow Tips

1. Start with `ccsinfo sessions list --active --json` to see current activity
2. Use `ccsinfo stats global --json` for an overview of all usage
3. Search with `ccsinfo search sessions "<query>" --json` to find specific topics
4. Drill into a session with `ccsinfo sessions messages <id> --json` for conversation details
5. Check `ccsinfo tasks pending --json` to see outstanding work across sessions
