"""Parser for Claude Code session files."""

from __future__ import annotations

import logging
import re
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pendulum
from pydantic import BaseModel, Field

from ccsinfo.core.parsers.jsonl import parse_jsonl
from ccsinfo.utils.paths import decode_project_path

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


class MessageContent(BaseModel):
    """Content within a message."""

    type: str
    text: str | None = None
    thinking: str | None = None
    tool_use_id: str | None = Field(default=None, alias="id")
    name: str | None = None
    input: dict[str, Any] | None = None
    signature: str | None = None

    model_config = {"populate_by_name": True, "extra": "allow"}


class Message(BaseModel):
    """A message within a conversation."""

    role: str
    content: str | list[MessageContent] | None = None
    model: str | None = None
    id: str | None = None
    type: str | None = None
    stop_reason: str | None = None
    usage: dict[str, Any] | None = None

    model_config = {"extra": "allow"}


class HookProgress(BaseModel):
    """Hook progress data."""

    type: str
    hook_event: str | None = Field(default=None, alias="hookEvent")
    hook_name: str | None = Field(default=None, alias="hookName")
    command: str | None = None

    model_config = {"populate_by_name": True, "extra": "allow"}


class SessionEntry(BaseModel):
    """A single entry in a session JSONL file."""

    type: str
    uuid: str | None = None
    parent_uuid: str | None = Field(default=None, alias="parentUuid")
    session_id: str | None = Field(default=None, alias="sessionId")
    timestamp: str | None = None
    cwd: str | None = None
    version: str | None = None
    git_branch: str | None = Field(default=None, alias="gitBranch")
    message: Message | None = None
    data: dict[str, Any] | None = None
    is_sidechain: bool | None = Field(default=None, alias="isSidechain")
    user_type: str | None = Field(default=None, alias="userType")
    request_id: str | None = Field(default=None, alias="requestId")
    tool_use_id: str | None = Field(default=None, alias="toolUseID")
    parent_tool_use_id: str | None = Field(default=None, alias="parentToolUseID")
    thinking_metadata: dict[str, Any] | None = Field(default=None, alias="thinkingMetadata")
    todos: list[Any] | None = None
    permission_mode: str | None = Field(default=None, alias="permissionMode")
    slug: str | None = None

    # For file-history-snapshot type
    message_id: str | None = Field(default=None, alias="messageId")
    snapshot: dict[str, Any] | None = None
    is_snapshot_update: bool | None = Field(default=None, alias="isSnapshotUpdate")

    model_config = {"populate_by_name": True, "extra": "allow"}

    def get_timestamp(self) -> datetime | None:
        """Parse and return the timestamp as a datetime object."""
        if self.timestamp:
            try:
                parsed = pendulum.parse(self.timestamp)
                if isinstance(parsed, pendulum.DateTime):
                    # Convert pendulum DateTime to standard datetime
                    return datetime.fromisoformat(parsed.isoformat())
            except Exception:
                return None
        return None


@dataclass
class Session:
    """Represents a parsed Claude Code session."""

    session_id: str
    file_path: Path
    entries: list[SessionEntry] = field(default_factory=list)

    @property
    def message_count(self) -> int:
        """Count of message entries (user + assistant)."""
        return sum(1 for e in self.entries if e.type in ("user", "assistant"))

    @property
    def user_message_count(self) -> int:
        """Count of user messages."""
        return sum(1 for e in self.entries if e.type == "user")

    @property
    def assistant_message_count(self) -> int:
        """Count of assistant messages."""
        return sum(1 for e in self.entries if e.type == "assistant")

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

    @property
    def first_timestamp(self) -> datetime | None:
        """Get the first timestamp in the session."""
        for entry in self.entries:
            ts = entry.get_timestamp()
            if ts:
                return ts
        return None

    @property
    def last_timestamp(self) -> datetime | None:
        """Get the last timestamp in the session."""
        for entry in reversed(self.entries):
            ts = entry.get_timestamp()
            if ts:
                return ts
        return None

    @property
    def duration(self) -> float | None:
        """Get the session duration in seconds."""
        first = self.first_timestamp
        last = self.last_timestamp
        if first and last:
            return (last - first).total_seconds()
        return None

    @property
    def cwd(self) -> str | None:
        """Get the working directory from the first entry that has it."""
        for entry in self.entries:
            if entry.cwd:
                return entry.cwd
        return None

    @property
    def version(self) -> str | None:
        """Get the Claude Code version from the session."""
        for entry in self.entries:
            if entry.version:
                return entry.version
        return None

    @property
    def git_branch(self) -> str | None:
        """Get the git branch from the session."""
        for entry in self.entries:
            if entry.git_branch:
                return entry.git_branch
        return None

    @property
    def slug(self) -> str | None:
        """Get the session slug if available."""
        for entry in self.entries:
            if entry.slug:
                return entry.slug
        return None

    def is_active(self) -> bool:
        """Check if this session is currently active."""
        return is_session_active(self.session_id)

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


def get_projects_directory() -> Path:
    """Get the Claude Code projects directory path.

    Returns:
        Path to ~/.claude/projects/
    """
    return Path.home() / ".claude" / "projects"


# Cache for active session IDs to avoid repeated pgrep calls
_active_sessions_cache: set[str] | None = None
_active_sessions_cache_time: float = 0.0
_CACHE_TTL_SECONDS: float = 5.0


def _get_active_session_ids() -> set[str]:
    """Get all active session IDs from running Claude processes.

    This function caches the result for a short time to avoid
    repeated expensive pgrep calls.

    Returns:
        Set of active session IDs.
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
            except (PermissionError, FileNotFoundError, OSError):
                continue

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.debug("Failed to get active sessions: %s", e)

    _active_sessions_cache = active_ids
    _active_sessions_cache_time = current_time
    return active_ids


def is_session_active(session_id: str) -> bool:
    """Check if a Claude Code session is currently running.

    This function uses a cached set of active session IDs for efficiency.

    Args:
        session_id: The session UUID to check.

    Returns:
        True if the session appears to be active, False otherwise.
    """
    return session_id in _get_active_session_ids()


def parse_session_file(file_path: Path) -> Session:
    """Parse a session JSONL file.

    Args:
        file_path: Path to the session JSONL file.

    Returns:
        Parsed Session object.
    """
    # Extract session ID from filename (remove .jsonl extension)
    session_id = file_path.stem

    entries: list[SessionEntry] = []
    for entry in parse_jsonl(file_path, SessionEntry, skip_malformed=True):
        if isinstance(entry, SessionEntry):
            entries.append(entry)

    return Session(
        session_id=session_id,
        file_path=file_path,
        entries=entries,
    )


def get_project_sessions(project_path: Path) -> Iterator[Session]:
    """Get all sessions for a project.

    Args:
        project_path: Path to the project's session directory.

    Yields:
        Session objects for each session file found.
    """
    if not project_path.exists():
        return

    for session_file in sorted(project_path.glob("*.jsonl")):
        # Skip history files
        if session_file.name.startswith("."):
            continue
        try:
            yield parse_session_file(session_file)
        except Exception as e:
            logger.warning("Failed to parse session file %s: %s", session_file, e)


def get_all_projects() -> Iterator[tuple[str, Path]]:
    """Get all projects with their encoded names and paths.

    Yields:
        Tuples of (decoded_project_path, project_directory_path).
    """
    projects_dir = get_projects_directory()
    if not projects_dir.exists():
        return

    for project_dir in sorted(projects_dir.iterdir()):
        if project_dir.is_dir():
            decoded_path = decode_project_path(project_dir.name)
            yield decoded_path, project_dir


def get_session_by_id(session_id: str) -> Session | None:
    """Find and parse a session by its ID across all projects.

    Args:
        session_id: The session UUID.

    Returns:
        Session object if found, None otherwise.
    """
    projects_dir = get_projects_directory()
    if not projects_dir.exists():
        return None

    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            session_file = project_dir / f"{session_id}.jsonl"
            if session_file.exists():
                return parse_session_file(session_file)

    return None


def get_all_sessions() -> Iterator[tuple[str, Session]]:
    """Get all sessions across all projects.

    Yields:
        Tuples of (project_path, Session).
    """
    for project_path, project_dir in get_all_projects():
        for session in get_project_sessions(project_dir):
            yield project_path, session


def get_session_summary(session: Session) -> dict[str, Any]:
    """Get a summary of session statistics.

    Args:
        session: The session to summarize.

    Returns:
        Dictionary containing session summary information.
    """
    return {
        "session_id": session.session_id,
        "file_path": str(session.file_path),
        "message_count": session.message_count,
        "user_messages": session.user_message_count,
        "assistant_messages": session.assistant_message_count,
        "tool_uses": session.tool_use_count,
        "first_timestamp": session.first_timestamp.isoformat() if session.first_timestamp else None,
        "last_timestamp": session.last_timestamp.isoformat() if session.last_timestamp else None,
        "duration_seconds": session.duration,
        "cwd": session.cwd,
        "version": session.version,
        "git_branch": session.git_branch,
        "slug": session.slug,
        "is_active": session.is_active(),
        "tools_used": sorted(session.get_unique_tools_used()),
    }
