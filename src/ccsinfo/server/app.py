"""Main FastAPI application for ccsinfo."""

from fastapi import FastAPI

from ccsinfo import __version__
from ccsinfo.server.routers import health, projects, search, sessions, stats, tasks

app = FastAPI(
    title="ccsinfo",
    description="Claude Code Session Info API",
    version=__version__,
)

# Include routers
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(health.router, tags=["health"])
