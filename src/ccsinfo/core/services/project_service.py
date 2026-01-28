"""Project service for managing Claude Code projects."""

from __future__ import annotations

import logging
from pathlib import Path

import pendulum

from ccsinfo.core.models.projects import Project
from ccsinfo.core.models.stats import ProjectStats
from ccsinfo.core.parsers.sessions import get_project_sessions, parse_session_file
from ccsinfo.utils.paths import (
    decode_project_path,
    list_all_projects,
    list_session_files,
)

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing Claude Code projects."""

    def list_projects(self) -> list[Project]:
        """List all projects.

        Returns:
            List of all projects with their metadata.
        """
        projects: list[Project] = []

        for project_dir in list_all_projects():
            project = self._parse_project_dir(project_dir)
            if project:
                projects.append(project)

        # Sort by last activity (most recent first)
        projects.sort(
            key=lambda p: p.last_activity or pendulum.datetime(1970, 1, 1),
            reverse=True,
        )

        return projects

    def get_project(self, project_id: str) -> Project | None:
        """Get a project by ID.

        Args:
            project_id: The Claude Code directory name (dash-encoded project path).

        Returns:
            Project object if found, None otherwise.
        """
        for project_dir in list_all_projects():
            if project_dir.name == project_id:
                return self._parse_project_dir(project_dir)

        return None

    def get_project_stats(self, project_id: str) -> ProjectStats | None:
        """Get statistics for a project.

        Args:
            project_id: The Claude Code directory name (dash-encoded project path).

        Returns:
            ProjectStats object if found, None otherwise.
        """
        project = self.get_project(project_id)
        if project is None:
            return None

        # Find the project directory
        project_dir = None
        for pdir in list_all_projects():
            if pdir.name == project_id:
                project_dir = pdir
                break

        if project_dir is None:
            return None

        # Calculate detailed stats
        total_messages = 0
        last_activity = None

        for session in get_project_sessions(project_dir):
            total_messages += session.message_count
            session_last = session.last_timestamp
            if session_last:
                session_dt = pendulum.instance(session_last)
                if last_activity is None or session_dt > last_activity:
                    last_activity = session_dt

        return ProjectStats(
            project_id=project_id,
            project_name=project.name,
            session_count=project.session_count,
            message_count=total_messages,
            last_activity=last_activity,
        )

    def _parse_project_dir(self, project_dir: Path) -> Project | None:
        """Parse a project directory into a Project object.

        Args:
            project_dir: Path to the project directory.

        Returns:
            Project object or None if parsing fails.
        """
        try:
            # The directory name is the encoded project path
            encoded = project_dir.name
            try:
                decoded = decode_project_path(encoded)
            except Exception:
                decoded = encoded

            # Count sessions
            session_files = list_session_files(project_dir)
            session_count = len(session_files)

            # Get last activity from most recent session
            last_activity = None
            for session_file in sorted(session_files, key=lambda f: f.stat().st_mtime, reverse=True):
                try:
                    session = parse_session_file(session_file)
                    if session.last_timestamp:
                        last_activity = pendulum.instance(session.last_timestamp)
                        break
                except Exception:
                    continue

            return Project(
                id=encoded,
                name=Path(decoded).name if decoded else "Unknown",
                path=decoded,
                session_count=session_count,
                last_activity=last_activity,
            )
        except Exception as e:
            logger.warning("Failed to parse project directory %s: %s", project_dir, e)
            return None


# Singleton instance
project_service = ProjectService()
