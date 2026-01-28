"""Task service for managing Claude Code tasks."""

from __future__ import annotations

import logging

from ccsinfo.core.models.tasks import Task, TaskStatus
from ccsinfo.core.parsers.tasks import (
    Task as ParsedTask,
)
from ccsinfo.core.parsers.tasks import (
    iter_all_session_tasks,
    parse_session_tasks,
)

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing Claude Code tasks."""

    def list_tasks(
        self,
        session_id: str | None = None,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        """List tasks with optional filters.

        Args:
            session_id: Optional session ID to filter by.
            status: Optional status filter.

        Returns:
            List of tasks matching the filters.
        """
        tasks: list[Task] = []

        if session_id is not None:
            # Get tasks for specific session
            collection = parse_session_tasks(session_id)
            for parsed_task in collection.tasks:
                task = self._convert_task(parsed_task)
                if status is None or task.status == status:
                    tasks.append(task)
        else:
            # Get all tasks from all sessions
            for collection in iter_all_session_tasks():
                for parsed_task in collection.tasks:
                    task = self._convert_task(parsed_task)
                    if status is None or task.status == status:
                        tasks.append(task)

        return tasks

    def get_task(self, task_id: str, session_id: str | None = None) -> Task | None:
        """Get a task by ID.

        Args:
            task_id: The task ID to find.
            session_id: The session ID to look in. If provided, only searches
                that session. If None, searches all sessions (returns first match).

        Returns:
            Task object if found, None otherwise.
        """
        if session_id is not None:
            collection = parse_session_tasks(session_id)
            parsed = collection.get_task_by_id(task_id)
            if parsed is not None:
                return self._convert_task(parsed)
            return None

        # Fallback: search all sessions (legacy behavior)
        for collection in iter_all_session_tasks():
            parsed = collection.get_task_by_id(task_id)
            if parsed is not None:
                return self._convert_task(parsed)

        return None

    def get_pending_tasks(self) -> list[Task]:
        """Get all pending tasks across all sessions.

        Returns:
            List of pending tasks.
        """
        return self.list_tasks(status=TaskStatus.PENDING)

    def get_session_tasks(self, session_id: str) -> list[Task]:
        """Get tasks for a specific session.

        Args:
            session_id: The session UUID.

        Returns:
            List of tasks for the session.
        """
        return self.list_tasks(session_id=session_id)

    def _convert_task(self, parsed: ParsedTask) -> Task:
        """Convert a parsed task to a Task model.

        Args:
            parsed: The parsed task from the parser.

        Returns:
            Task model instance.
        """
        # Map status string to enum
        status_map = {
            "pending": TaskStatus.PENDING,
            "in_progress": TaskStatus.IN_PROGRESS,
            "completed": TaskStatus.COMPLETED,
        }
        status = status_map.get(parsed.status, TaskStatus.PENDING)

        return Task(
            id=parsed.id,
            subject=parsed.subject,
            description=parsed.description,
            status=status,
            owner=parsed.owner,
            blocked_by=parsed.blocked_by,
            blocks=parsed.blocks,
            active_form=parsed.active_form,
            metadata=parsed.metadata or {},
        )


# Singleton instance
task_service = TaskService()
