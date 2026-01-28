"""Task management API routes."""

from fastapi import APIRouter, HTTPException, Query

from ccsinfo.core.models.tasks import Task, TaskStatus
from ccsinfo.core.services import task_service

router = APIRouter()


@router.get("", response_model=list[Task])
async def list_tasks(
    session_id: str | None = Query(None),
    status: str | None = Query(None),
) -> list[Task]:
    """List all tasks."""
    status_enum: TaskStatus | None = None
    if status:
        try:
            status_enum = TaskStatus(status)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Valid values: pending, in_progress, completed",
            ) from e
    return task_service.list_tasks(session_id=session_id, status=status_enum)


@router.get("/pending", response_model=list[Task])
async def pending_tasks() -> list[Task]:
    """List pending tasks."""
    return task_service.get_pending_tasks()


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    session_id: str = Query(..., description="Session ID (required since task IDs are only unique within a session)"),
) -> Task:
    """Get task details."""
    task = task_service.get_task(task_id, session_id=session_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
