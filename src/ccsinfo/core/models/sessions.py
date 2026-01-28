"""Models for Claude Code sessions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import Field

from ccsinfo.core.models.base import BaseORJSONModel
from ccsinfo.core.models.messages import Message


class SessionSummary(BaseORJSONModel):
    """Lightweight session summary for listings."""

    id: str
    project_path: str
    project_name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    message_count: int = 0
    is_active: bool = False


class Session(BaseORJSONModel):
    """A Claude Code session."""

    id: str
    project_path: str
    project_name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    message_count: int = 0
    is_active: bool = False
    file_path: Path | None = None

    def to_summary(self) -> SessionSummary:
        """Convert to a lightweight summary."""
        return SessionSummary(
            id=self.id,
            project_path=self.project_path,
            project_name=self.project_name,
            created_at=self.created_at,
            updated_at=self.updated_at,
            message_count=self.message_count,
            is_active=self.is_active,
        )


class SessionDetail(BaseORJSONModel):
    """Full session with messages."""

    id: str
    project_path: str
    project_name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    message_count: int = 0
    is_active: bool = False
    file_path: Path | None = None
    messages: list[Message] = Field(default_factory=list)

    @property
    def tool_call_count(self) -> int:
        """Count total tool calls in the session."""
        return sum(len(msg.tool_calls) for msg in self.messages)

    @property
    def user_messages(self) -> list[Message]:
        """Get all user messages."""
        return [msg for msg in self.messages if msg.type == "user"]

    @property
    def assistant_messages(self) -> list[Message]:
        """Get all assistant messages."""
        return [msg for msg in self.messages if msg.type == "assistant"]
