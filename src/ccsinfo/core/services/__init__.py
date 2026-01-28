"""Service modules for business logic."""

from ccsinfo.core.services.project_service import ProjectService, project_service
from ccsinfo.core.services.search_service import SearchService, search_service
from ccsinfo.core.services.session_service import SessionService, session_service
from ccsinfo.core.services.stats_service import StatsService, stats_service
from ccsinfo.core.services.task_service import TaskService, task_service

__all__ = [
    "ProjectService",
    "SearchService",
    "SessionService",
    "StatsService",
    "TaskService",
    "project_service",
    "search_service",
    "session_service",
    "stats_service",
    "task_service",
]
