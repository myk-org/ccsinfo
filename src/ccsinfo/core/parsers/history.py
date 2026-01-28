"""Parser for Claude Code prompt history files."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pendulum
from pydantic import BaseModel, Field

from ccsinfo.core.parsers.jsonl import parse_jsonl
from ccsinfo.core.parsers.sessions import get_projects_directory
from ccsinfo.utils.paths import decode_project_path

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


class HistoryEntry(BaseModel):
    """A single entry in a prompt history file."""

    prompt: str | None = None
    timestamp: str | None = None
    session_id: str | None = Field(default=None, alias="sessionId")
    cwd: str | None = None
    version: str | None = None

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
class PromptHistory:
    """Collection of prompt history entries for a project."""

    project_path: str
    file_path: Path
    entries: list[HistoryEntry] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        """Total number of history entries."""
        return len(self.entries)

    @property
    def first_timestamp(self) -> datetime | None:
        """Get the first timestamp in the history."""
        for entry in self.entries:
            ts = entry.get_timestamp()
            if ts:
                return ts
        return None

    @property
    def last_timestamp(self) -> datetime | None:
        """Get the last timestamp in the history."""
        for entry in reversed(self.entries):
            ts = entry.get_timestamp()
            if ts:
                return ts
        return None

    def get_entries_by_session(self, session_id: str) -> list[HistoryEntry]:
        """Get all history entries for a specific session.

        Args:
            session_id: The session UUID to filter by.

        Returns:
            List of history entries for that session.
        """
        return [e for e in self.entries if e.session_id == session_id]

    def get_unique_sessions(self) -> set[str]:
        """Get set of unique session IDs in the history.

        Returns:
            Set of session UUIDs.
        """
        return {e.session_id for e in self.entries if e.session_id}

    def search_prompts(self, query: str, *, case_sensitive: bool = False) -> list[HistoryEntry]:
        """Search for prompts containing a query string.

        Args:
            query: The search query.
            case_sensitive: Whether the search should be case-sensitive.

        Returns:
            List of matching history entries.
        """
        results: list[HistoryEntry] = []
        search_query = query if case_sensitive else query.lower()

        for entry in self.entries:
            if entry.prompt:
                prompt_text = entry.prompt if case_sensitive else entry.prompt.lower()
                if search_query in prompt_text:
                    results.append(entry)

        return results


def get_history_file(project_dir: Path) -> Path:
    """Get the path to the history file for a project.

    Args:
        project_dir: Path to the project's Claude directory.

    Returns:
        Path to the .history.jsonl file.
    """
    return project_dir / ".history.jsonl"


def parse_history_file(file_path: Path, project_path: str = "") -> PromptHistory:
    """Parse a prompt history JSONL file.

    Args:
        file_path: Path to the .history.jsonl file.
        project_path: The decoded project path for reference.

    Returns:
        Parsed PromptHistory object.
    """
    entries: list[HistoryEntry] = []

    if not file_path.exists():
        return PromptHistory(
            project_path=project_path,
            file_path=file_path,
            entries=[],
        )

    for entry in parse_jsonl(file_path, HistoryEntry, skip_malformed=True):
        if isinstance(entry, HistoryEntry):
            entries.append(entry)

    return PromptHistory(
        project_path=project_path,
        file_path=file_path,
        entries=entries,
    )


def get_project_history(project_dir: Path, project_path: str = "") -> PromptHistory:
    """Get the prompt history for a project.

    Args:
        project_dir: Path to the project's Claude directory.
        project_path: The decoded project path for reference.

    Returns:
        PromptHistory for the project.
    """
    history_file = get_history_file(project_dir)
    return parse_history_file(history_file, project_path)


def get_all_history() -> Iterator[PromptHistory]:
    """Get prompt history for all projects.

    Yields:
        PromptHistory for each project that has a history file.
    """
    projects_dir = get_projects_directory()
    if not projects_dir.exists():
        return

    for project_dir in sorted(projects_dir.iterdir()):
        if project_dir.is_dir():
            history_file = get_history_file(project_dir)
            if history_file.exists():
                project_path = decode_project_path(project_dir.name)
                try:
                    yield parse_history_file(history_file, project_path)
                except Exception as e:
                    logger.warning("Failed to parse history file %s: %s", history_file, e)


def search_all_history(query: str, *, case_sensitive: bool = False) -> list[tuple[str, HistoryEntry]]:
    """Search for prompts across all project histories.

    Args:
        query: The search query.
        case_sensitive: Whether the search should be case-sensitive.

    Returns:
        List of tuples (project_path, HistoryEntry) for matching entries.
    """
    results: list[tuple[str, HistoryEntry]] = []

    for history in get_all_history():
        matches = history.search_prompts(query, case_sensitive=case_sensitive)
        for entry in matches:
            results.append((history.project_path, entry))

    return results


def get_history_summary(history: PromptHistory) -> dict[str, Any]:
    """Get a summary of prompt history statistics.

    Args:
        history: The history to summarize.

    Returns:
        Dictionary containing history summary information.
    """
    unique_sessions = history.get_unique_sessions()
    return {
        "project_path": history.project_path,
        "file_path": str(history.file_path),
        "total_prompts": history.total_count,
        "unique_sessions": len(unique_sessions),
        "session_ids": sorted(unique_sessions),
        "first_timestamp": history.first_timestamp.isoformat() if history.first_timestamp else None,
        "last_timestamp": history.last_timestamp.isoformat() if history.last_timestamp else None,
    }
