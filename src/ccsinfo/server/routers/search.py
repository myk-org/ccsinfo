"""Search API routes."""

from typing import Any

from fastapi import APIRouter, Query

from ccsinfo.core.models.sessions import SessionSummary
from ccsinfo.core.services import search_service

router = APIRouter()


@router.get("", response_model=list[SessionSummary])
async def search_sessions(
    q: str = Query(..., description="Search query"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
) -> list[SessionSummary]:
    """Full-text search across sessions."""
    return search_service.search_sessions(q, limit=limit)


@router.get("/messages")
async def search_messages(
    q: str = Query(..., description="Search query"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
) -> list[dict[str, Any]]:
    """Search message content across all sessions."""
    return search_service.search_messages(q, limit=limit)


@router.get("/history")
async def search_history(
    q: str = Query(..., description="Search query"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
) -> list[dict[str, Any]]:
    """Search prompt history."""
    return search_service.search_history(q, limit=limit)
