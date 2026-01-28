"""Models for statistics and analytics."""

from __future__ import annotations

import datetime as dt

from ccsinfo.core.models.base import BaseORJSONModel


class GlobalStats(BaseORJSONModel):
    """Global statistics across all sessions and projects."""

    total_sessions: int = 0
    total_projects: int = 0
    total_messages: int = 0
    total_tool_calls: int = 0


class DailyStats(BaseORJSONModel):
    """Statistics for a single day."""

    date: dt.date | None = None
    session_count: int = 0
    message_count: int = 0


class ProjectStats(BaseORJSONModel):
    """Statistics for a single project."""

    project_id: str
    project_name: str
    session_count: int = 0
    message_count: int = 0
    last_activity: dt.datetime | None = None
