"""Models for Claude Code projects."""

from __future__ import annotations

from datetime import datetime

from ccsinfo.core.models.base import BaseORJSONModel


class Project(BaseORJSONModel):
    """A Claude Code project (directory with sessions)."""

    id: str  # URL-encoded path used as directory name
    name: str  # Human-readable project name
    path: str  # Original project path
    session_count: int = 0
    last_activity: datetime | None = None
