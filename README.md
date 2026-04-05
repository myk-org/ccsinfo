# ccsinfo

A CLI and REST API for viewing and analyzing Claude Code session data.

**Full documentation:** <https://myk-org.github.io/ccsinfo/>

## Quick Start

```bash
uv tool install ccsinfo
ccsinfo sessions list
ccsinfo sessions show <session-id>
```

## Claude Code Skill

To make the skill available to Claude Code, copy the `ccsinfo` folder to your skills directory:

```bash
cp -r ccsinfo ~/.claude/skills/
```

## OpenClaw Skill

An OpenClaw skill is available for AI assistants to query Claude Code sessions remotely.

**Install via ClawHub:**

```bash
clawhub install ccsinfo
```

**Skill page:** https://clawhub.ai/myakove/ccsinfo

The skill allows AI assistants running in OpenClaw to:
- Query and analyze Claude Code session data via the ccsinfo REST API
- View conversation history, tool calls, and tasks
- Search sessions and track project statistics
- Monitor active sessions and progress

**Requirements:**
- ccsinfo server running (`ccsinfo serve`)
- `CCSINFO_SERVER_URL` environment variable set to your server

**Example usage:** Ask your OpenClaw assistant: *"Show my active Claude Code sessions"* or *"What were the recent tasks in my main project?"*

---

See the [full documentation](https://myk-org.github.io/ccsinfo/) for everything else.

## License

MIT License. See [LICENSE](LICENSE) for details.
