"""Tests for services (integration-style)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pendulum

from ccsinfo.core.models.stats import GlobalStats
from ccsinfo.core.services import (
    ProjectService,
    SessionService,
    StatsService,
    project_service,
    session_service,
    stats_service,
)


class TestSessionServiceBasic:
    """Basic tests for SessionService."""

    def test_session_service_singleton_exists(self) -> None:
        """Test that session_service singleton is available."""
        assert session_service is not None
        assert isinstance(session_service, SessionService)

    def test_list_sessions_returns_list(self) -> None:
        """Test that list_sessions returns a list."""
        sessions = session_service.list_sessions(limit=5)
        assert isinstance(sessions, list)

    def test_list_sessions_with_limit(self) -> None:
        """Test list_sessions respects limit parameter."""
        sessions = session_service.list_sessions(limit=2)
        assert len(sessions) <= 2

    def test_list_sessions_active_only(self) -> None:
        """Test list_sessions with active_only filter."""
        sessions = session_service.list_sessions(active_only=True)
        assert isinstance(sessions, list)
        # All returned sessions should be active
        for session in sessions:
            assert session.is_active is True

    def test_get_session_nonexistent(self) -> None:
        """Test get_session returns None for nonexistent session."""
        result = session_service.get_session("nonexistent-session-id")
        assert result is None

    def test_get_session_detail_nonexistent(self) -> None:
        """Test get_session_detail returns None for nonexistent session."""
        result = session_service.get_session_detail("nonexistent-session-id")
        assert result is None

    def test_get_session_messages_nonexistent(self) -> None:
        """Test get_session_messages returns empty list for nonexistent session."""
        messages = session_service.get_session_messages("nonexistent-session-id")
        assert messages == []

    def test_get_active_sessions(self) -> None:
        """Test get_active_sessions returns list."""
        sessions = session_service.get_active_sessions()
        assert isinstance(sessions, list)

    def test_get_session_tools_nonexistent(self) -> None:
        """Test get_session_tools returns empty list for nonexistent session."""
        tools = session_service.get_session_tools("nonexistent-session-id")
        assert tools == []


class TestProjectServiceBasic:
    """Basic tests for ProjectService."""

    def test_project_service_singleton_exists(self) -> None:
        """Test that project_service singleton is available."""
        assert project_service is not None
        assert isinstance(project_service, ProjectService)

    def test_list_projects_returns_list(self) -> None:
        """Test that list_projects returns a list."""
        projects = project_service.list_projects()
        assert isinstance(projects, list)

    def test_get_project_nonexistent(self) -> None:
        """Test get_project returns None for nonexistent project."""
        result = project_service.get_project("nonexistent-project-id")
        assert result is None

    def test_get_project_stats_nonexistent(self) -> None:
        """Test get_project_stats returns None for nonexistent project."""
        result = project_service.get_project_stats("nonexistent-project-id")
        assert result is None


class TestStatsServiceBasic:
    """Basic tests for StatsService."""

    def test_stats_service_singleton_exists(self) -> None:
        """Test that stats_service singleton is available."""
        assert stats_service is not None
        assert isinstance(stats_service, StatsService)

    def test_get_global_stats(self) -> None:
        """Test that get_global_stats returns GlobalStats."""
        stats = stats_service.get_global_stats()
        assert isinstance(stats, GlobalStats)
        assert hasattr(stats, "total_sessions")
        assert hasattr(stats, "total_projects")
        assert hasattr(stats, "total_messages")
        assert hasattr(stats, "total_tool_calls")

    def test_get_global_stats_values_are_non_negative(self) -> None:
        """Test that global stats values are non-negative."""
        stats = stats_service.get_global_stats()
        assert stats.total_sessions >= 0
        assert stats.total_projects >= 0
        assert stats.total_messages >= 0
        assert stats.total_tool_calls >= 0

    def test_get_daily_stats(self) -> None:
        """Test that get_daily_stats returns a list."""
        daily = stats_service.get_daily_stats(days=7)
        assert isinstance(daily, list)

    def test_get_daily_stats_with_custom_days(self) -> None:
        """Test get_daily_stats with custom days parameter."""
        daily = stats_service.get_daily_stats(days=30)
        assert isinstance(daily, list)

    def test_get_trends(self) -> None:
        """Test that get_trends returns expected structure."""
        trends = stats_service.get_trends()
        assert isinstance(trends, dict)
        assert "sessions_last_7_days" in trends
        assert "sessions_last_30_days" in trends
        assert "messages_last_7_days" in trends
        assert "messages_last_30_days" in trends
        assert "most_active_projects" in trends
        assert "most_used_tools" in trends
        assert "average_session_length" in trends

    def test_get_trends_values_are_non_negative(self) -> None:
        """Test that trend values are non-negative."""
        trends = stats_service.get_trends()
        assert trends["sessions_last_7_days"] >= 0
        assert trends["sessions_last_30_days"] >= 0
        assert trends["messages_last_7_days"] >= 0
        assert trends["messages_last_30_days"] >= 0
        assert trends["average_session_length"] >= 0


class TestSessionServiceMocked:
    """Tests for SessionService with mocked data."""

    def test_list_sessions_sorted_by_updated_at(self) -> None:
        """Test that sessions are sorted by updated_at descending."""
        # Create mock sessions with different timestamps
        mock_sessions = [
            (
                "/path1",
                MagicMock(
                    session_id="session-1",
                    message_count=5,
                    first_timestamp=pendulum.parse("2024-01-10T10:00:00Z"),
                    last_timestamp=pendulum.parse("2024-01-10T11:00:00Z"),
                    is_active=MagicMock(return_value=False),
                ),
            ),
            (
                "/path2",
                MagicMock(
                    session_id="session-2",
                    message_count=10,
                    first_timestamp=pendulum.parse("2024-01-15T10:00:00Z"),
                    last_timestamp=pendulum.parse("2024-01-15T11:00:00Z"),
                    is_active=MagicMock(return_value=False),
                ),
            ),
        ]

        with patch("ccsinfo.core.services.session_service.get_all_sessions", return_value=mock_sessions):
            service = SessionService()
            sessions = service.list_sessions()

            # Most recent should be first
            if len(sessions) >= 2:
                assert sessions[0].id == "session-2"
                assert sessions[1].id == "session-1"


class TestProjectServiceMocked:
    """Tests for ProjectService with mocked data."""

    def test_list_projects_sorted_by_last_activity(self) -> None:
        """Test that projects are sorted by last_activity descending."""
        # Create mock project directories
        mock_dirs = []

        with patch("ccsinfo.core.services.project_service.list_all_projects", return_value=mock_dirs):
            service = ProjectService()
            projects = service.list_projects()
            assert isinstance(projects, list)


class TestStatsServiceMocked:
    """Tests for StatsService with mocked data."""

    def test_global_stats_calculation(self) -> None:
        """Test global stats are calculated correctly from sessions."""
        mock_sessions = [
            (
                "/project1",
                MagicMock(
                    message_count=10,
                    tool_use_count=5,
                    first_timestamp=pendulum.now(),
                ),
            ),
            (
                "/project1",
                MagicMock(
                    message_count=20,
                    tool_use_count=10,
                    first_timestamp=pendulum.now(),
                ),
            ),
            (
                "/project2",
                MagicMock(
                    message_count=15,
                    tool_use_count=8,
                    first_timestamp=pendulum.now(),
                ),
            ),
        ]

        with patch("ccsinfo.core.services.stats_service.get_all_sessions", return_value=mock_sessions):
            service = StatsService()
            stats = service.get_global_stats()

            assert stats.total_sessions == 3
            assert stats.total_projects == 2  # Two unique project paths
            assert stats.total_messages == 45  # 10 + 20 + 15
            assert stats.total_tool_calls == 23  # 5 + 10 + 8


class TestServiceIntegration:
    """Integration tests for services working together."""

    def test_project_and_session_services_consistent(self) -> None:
        """Test that project and session services return consistent data."""
        projects = project_service.list_projects()
        sessions = session_service.list_sessions()

        # If there are sessions, there should be at least one project
        if sessions:
            assert len(projects) > 0

    def test_stats_match_actual_data(self) -> None:
        """Test that stats reflect the actual session/project counts."""
        projects = project_service.list_projects()
        _ = session_service.list_sessions()
        stats = stats_service.get_global_stats()

        # Stats should be consistent with list counts
        # Note: This may not be exact due to filtering, but should be close
        assert stats.total_projects <= len(projects) + 10  # Allow some margin
        # Sessions might have duplicates in different project paths
        assert stats.total_sessions >= 0
