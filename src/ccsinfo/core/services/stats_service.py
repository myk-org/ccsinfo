"""Statistics service for Claude Code analytics."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

import pendulum

from ccsinfo.core.models.stats import DailyStats, GlobalStats
from ccsinfo.core.parsers.sessions import get_all_sessions

logger = logging.getLogger(__name__)


class StatsService:
    """Service for calculating Claude Code usage statistics."""

    def get_global_stats(self) -> GlobalStats:
        """Get global usage statistics across all sessions and projects.

        Returns:
            GlobalStats object with totals.
        """
        total_sessions = 0
        total_projects = 0
        total_messages = 0
        total_tool_calls = 0

        project_ids = set()

        for project_path, session in get_all_sessions():
            total_sessions += 1
            project_ids.add(project_path)
            total_messages += session.message_count
            total_tool_calls += session.tool_use_count

        total_projects = len(project_ids)

        return GlobalStats(
            total_sessions=total_sessions,
            total_projects=total_projects,
            total_messages=total_messages,
            total_tool_calls=total_tool_calls,
        )

    def get_daily_stats(self, days: int = 30) -> list[DailyStats]:
        """Get daily activity breakdown for the last N days.

        Args:
            days: Number of days to include in the stats.

        Returns:
            List of DailyStats objects, one per day with activity.
        """
        now = pendulum.now()
        cutoff = now.subtract(days=days)

        # Aggregate by date
        daily_data: dict[str, dict[str, int]] = defaultdict(lambda: {"session_count": 0, "message_count": 0})

        for _project_path, session in get_all_sessions():
            # Use the session's first timestamp as the activity date
            ts = session.first_timestamp
            if ts is None:
                continue

            session_dt = pendulum.instance(ts)
            if session_dt < cutoff:
                continue

            date_key = session_dt.format("YYYY-MM-DD")
            daily_data[date_key]["session_count"] += 1
            daily_data[date_key]["message_count"] += session.message_count

        # Convert to DailyStats objects
        results: list[DailyStats] = []
        for date_str, data in sorted(daily_data.items()):
            parsed_dt = pendulum.parse(date_str)
            date = parsed_dt.date() if parsed_dt else None
            results.append(
                DailyStats(
                    date=date,
                    session_count=data["session_count"],
                    message_count=data["message_count"],
                )
            )

        return results

    def get_trends(self) -> dict[str, Any]:
        """Get usage trends over time.

        Returns:
            Dictionary containing trend analysis:
            - sessions_last_7_days: Session count in the last 7 days
            - sessions_last_30_days: Session count in the last 30 days
            - messages_last_7_days: Message count in the last 7 days
            - messages_last_30_days: Message count in the last 30 days
            - most_active_projects: Top 5 most active projects
            - most_used_tools: Top 10 most used tools
            - average_session_length: Average messages per session
        """
        now = pendulum.now()
        cutoff_7 = now.subtract(days=7)
        cutoff_30 = now.subtract(days=30)

        sessions_7 = 0
        sessions_30 = 0
        messages_7 = 0
        messages_30 = 0

        project_activity: dict[str, int] = defaultdict(int)
        tool_usage: dict[str, int] = defaultdict(int)
        total_sessions = 0
        total_messages = 0

        for project_path, session in get_all_sessions():
            total_sessions += 1
            total_messages += session.message_count
            project_activity[project_path] += session.message_count

            # Collect tool usage
            for tool in session.get_unique_tools_used():
                tool_usage[tool] += 1

            ts = session.first_timestamp
            if ts is not None:
                session_dt = pendulum.instance(ts)
                if session_dt >= cutoff_30:
                    sessions_30 += 1
                    messages_30 += session.message_count
                    if session_dt >= cutoff_7:
                        sessions_7 += 1
                        messages_7 += session.message_count

        # Calculate most active projects
        most_active = sorted(
            project_activity.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        # Calculate most used tools
        most_used_tools = sorted(
            tool_usage.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        # Average session length
        avg_length = total_messages / total_sessions if total_sessions > 0 else 0

        return {
            "sessions_last_7_days": sessions_7,
            "sessions_last_30_days": sessions_30,
            "messages_last_7_days": messages_7,
            "messages_last_30_days": messages_30,
            "most_active_projects": [{"project": p, "message_count": c} for p, c in most_active],
            "most_used_tools": [{"tool": t, "count": c} for t, c in most_used_tools],
            "average_session_length": round(avg_length, 2),
        }


# Singleton instance
stats_service = StatsService()
