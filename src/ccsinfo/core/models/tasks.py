"""Models for Claude Code tasks."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from ccsinfo.core.models.base import BaseORJSONModel


class TaskStatus(StrEnum):
    """Task status enum."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Task(BaseORJSONModel):
    """A Claude Code task from ~/.claude/tasks/<session-uuid>/*.json."""

    id: str
    subject: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    owner: str | None = None
    blocked_by: list[str] = Field(default_factory=list, alias="blockedBy")
    blocks: list[str] = Field(default_factory=list)
    active_form: str | None = Field(default=None, alias="activeForm")
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @property
    def is_blocked(self) -> bool:
        """Check if task is blocked by other tasks."""
        return len(self.blocked_by) > 0

    @property
    def is_complete(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.COMPLETED
