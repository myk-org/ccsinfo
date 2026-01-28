"""Health check API routes."""

from typing import Any

from fastapi import APIRouter

from ccsinfo import __version__
from ccsinfo.core.services import stats_service

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/info")
async def info() -> dict[str, Any]:
    """Server info endpoint."""
    stats = stats_service.get_global_stats()
    return {
        "version": __version__,
        "total_sessions": stats.total_sessions,
        "total_projects": stats.total_projects,
    }
