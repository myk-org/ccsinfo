"""Statistics API routes."""

from typing import Any

from fastapi import APIRouter, Query

from ccsinfo.core.models.stats import DailyStats, GlobalStats
from ccsinfo.core.services import stats_service

router = APIRouter()


@router.get("", response_model=GlobalStats)
async def global_stats() -> GlobalStats:
    """Get global usage statistics."""
    return stats_service.get_global_stats()


@router.get("/daily", response_model=list[DailyStats])
async def daily_stats(days: int = Query(30, ge=1, le=365)) -> list[DailyStats]:
    """Get daily activity breakdown."""
    return stats_service.get_daily_stats(days=days)


@router.get("/trends")
async def trends() -> dict[str, Any]:
    """Get usage trends over time."""
    return stats_service.get_trends()
