"""Session management API routes."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ccsinfo.core.models.sessions import Session, SessionSummary
from ccsinfo.core.services import session_service, task_service

router = APIRouter()


@router.get("", response_model=list[SessionSummary])
async def list_sessions(
    project_id: str | None = Query(None, description="Filter by project"),
    active_only: bool = Query(False, description="Show only active sessions"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
) -> list[SessionSummary]:
    """List all sessions."""
    return session_service.list_sessions(project_id=project_id, active_only=active_only, limit=limit)


@router.get("/active", response_model=list[SessionSummary])
async def active_sessions() -> list[SessionSummary]:
    """List currently running sessions."""
    return session_service.get_active_sessions()


@router.get("/{session_id}", response_model=Session)
async def get_session(session_id: str) -> Session:
    """Get session details."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{session_id}/messages")
async def get_messages(
    session_id: str,
    role: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
) -> list[dict[str, Any]]:
    """Get messages from a session."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = session_service.get_session_messages(session_id, role=role, limit=limit)
    return [msg.model_dump(mode="json") for msg in messages]


@router.get("/{session_id}/tools")
async def get_tools(session_id: str) -> list[dict[str, Any]]:
    """Get tool calls from a session."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_service.get_session_tools(session_id)


@router.get("/{session_id}/tasks")
async def get_session_tasks(session_id: str) -> list[dict[str, Any]]:
    """Get tasks for a session."""
    tasks = task_service.get_session_tasks(session_id)
    return [t.model_dump(mode="json") for t in tasks]


@router.get("/{session_id}/progress")
async def get_progress(session_id: str) -> dict[str, Any]:
    """Get session progress (status, last activity, active tasks)."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    tasks = task_service.get_session_tasks(session_id)
    active_tasks = [t for t in tasks if t.status.value == "in_progress"]
    return {
        "session_id": session_id,
        "is_active": session.is_active,
        "last_activity": session.updated_at.isoformat() if session.updated_at else None,
        "message_count": session.message_count,
        "active_tasks": [t.model_dump(mode="json") for t in active_tasks],
    }


@router.get("/{session_id}/summary")
async def get_summary(session_id: str) -> dict[str, Any]:
    """Get brief session summary."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    result: dict[str, Any] = session.to_summary().model_dump(mode="json")
    return result
