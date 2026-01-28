"""Project management API routes."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ccsinfo.core.models.projects import Project
from ccsinfo.core.models.sessions import SessionSummary
from ccsinfo.core.models.stats import ProjectStats
from ccsinfo.core.services import project_service, session_service

router = APIRouter()


@router.get("", response_model=list[Project])
async def list_projects() -> list[Project]:
    """List all projects."""
    return project_service.list_projects()


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str) -> Project:
    """Get project details."""
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/sessions", response_model=list[SessionSummary])
async def get_project_sessions(
    project_id: str,
    limit: int = Query(50, ge=1, le=500),
) -> list[SessionSummary]:
    """Get sessions for a project."""
    return session_service.list_sessions(project_id=project_id, limit=limit)


@router.get("/{project_id}/sessions/active", response_model=list[SessionSummary])
async def get_project_active_sessions(project_id: str) -> list[SessionSummary]:
    """Get active sessions for a project."""
    return session_service.list_sessions(project_id=project_id, active_only=True)


@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(project_id: str) -> ProjectStats | dict[str, Any]:
    """Get project statistics."""
    stats = project_service.get_project_stats(project_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Project not found")
    return stats
