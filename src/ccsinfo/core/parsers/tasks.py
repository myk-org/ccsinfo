"""Parser for Claude Code task files."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from ccsinfo.core.parsers.jsonl import iter_json_files, parse_json_as

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


class Task(BaseModel):
    """Represents a Claude Code task."""

    id: str
    subject: str
    description: str = ""
    active_form: str | None = Field(default=None, alias="activeForm")
    status: str = "pending"
    blocks: list[str] = Field(default_factory=list)
    blocked_by: list[str] = Field(default_factory=list, alias="blockedBy")
    owner: str | None = None
    metadata: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


@dataclass
class TaskCollection:
    """A collection of tasks from a session."""

    session_id: str
    tasks: list[Task] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        """Total number of tasks."""
        return len(self.tasks)

    @property
    def pending_count(self) -> int:
        """Number of pending tasks."""
        return sum(1 for t in self.tasks if t.status == "pending")

    @property
    def in_progress_count(self) -> int:
        """Number of in-progress tasks."""
        return sum(1 for t in self.tasks if t.status == "in_progress")

    @property
    def completed_count(self) -> int:
        """Number of completed tasks."""
        return sum(1 for t in self.tasks if t.status == "completed")

    def get_task_by_id(self, task_id: str) -> Task | None:
        """Get a task by its ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_blocked_tasks(self) -> list[Task]:
        """Get all tasks that are blocked by other tasks."""
        return [t for t in self.tasks if t.blocked_by]

    def get_ready_tasks(self) -> list[Task]:
        """Get all pending tasks that are not blocked."""
        return [t for t in self.tasks if t.status == "pending" and not t.blocked_by]


def get_tasks_directory() -> Path:
    """Get the Claude Code tasks directory path.

    Returns:
        Path to ~/.claude/tasks/
    """
    return Path.home() / ".claude" / "tasks"


def parse_task_file(file_path: Path) -> Task | None:
    """Parse a single task JSON file.

    Args:
        file_path: Path to the task JSON file.

    Returns:
        Parsed Task or None if parsing fails.
    """
    try:
        return parse_json_as(file_path, Task)
    except Exception as e:
        logger.warning("Failed to parse task file %s: %s", file_path, e)
        return None


def parse_session_tasks(session_id: str) -> TaskCollection:
    """Parse all tasks for a given session.

    Args:
        session_id: The session UUID.

    Returns:
        TaskCollection containing all parsed tasks.
    """
    tasks_dir = get_tasks_directory() / session_id
    tasks: list[Task] = []

    if not tasks_dir.exists():
        logger.debug("No tasks directory found for session %s", session_id)
        return TaskCollection(session_id=session_id, tasks=[])

    for task_file in iter_json_files(tasks_dir, "*.json"):
        task = parse_task_file(task_file)
        if task is not None:
            tasks.append(task)

    # Sort by ID (numeric sort if possible)
    tasks.sort(key=lambda t: (int(t.id) if t.id.isdigit() else float("inf"), t.id))

    return TaskCollection(session_id=session_id, tasks=tasks)


def iter_all_session_tasks() -> Iterator[TaskCollection]:
    """Iterate over task collections for all sessions.

    Yields:
        TaskCollection for each session that has tasks.
    """
    tasks_dir = get_tasks_directory()
    if not tasks_dir.exists():
        return

    for session_dir in sorted(tasks_dir.iterdir()):
        if session_dir.is_dir():
            session_id = session_dir.name
            collection = parse_session_tasks(session_id)
            if collection.total_count > 0:
                yield collection


def get_session_ids_with_tasks() -> list[str]:
    """Get list of session IDs that have task files.

    Returns:
        List of session UUIDs with tasks.
    """
    tasks_dir = get_tasks_directory()
    if not tasks_dir.exists():
        return []

    return [d.name for d in sorted(tasks_dir.iterdir()) if d.is_dir() and any(d.glob("*.json"))]
