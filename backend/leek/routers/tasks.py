import asyncio
from functools import partial

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from leek import celery_client
from leek.db import get_session
from leek.models import Task, TaskEvent
from leek.schemas import PaginatedResponse, TaskDetail, TaskEventSchema, TaskSummary

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=PaginatedResponse)
async def list_tasks(
    state: str | None = None,
    name: str | None = None,
    worker: str | None = None,
    search: str | None = None,
    sort_by: str = "last_updated",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    query = select(Task)

    if state:
        query = query.where(Task.state == state)
    if name:
        query = query.where(Task.name == name)
    if worker:
        query = query.where(Task.worker == worker)
    if search:
        query = query.where(
            Task.name.ilike(f"%{search}%") | Task.uuid.ilike(f"%{search}%")
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    # Sort
    sort_col = getattr(Task, sort_by, Task.last_updated)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    tasks = result.scalars().all()

    return PaginatedResponse(
        items=[TaskSummary.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/names", response_model=list[str])
async def list_task_names(session: AsyncSession = Depends(get_session)):
    """Get all distinct task names for filtering."""
    result = await session.execute(
        select(Task.name).where(Task.name.isnot(None)).distinct().order_by(Task.name)
    )
    return [row[0] for row in result.all()]


@router.get("/{task_id}", response_model=TaskDetail)
async def get_task(task_id: str, session: AsyncSession = Depends(get_session)):
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskDetail.model_validate(task)


@router.get("/{task_id}/events", response_model=list[TaskEventSchema])
async def get_task_events(task_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(TaskEvent)
        .where(TaskEvent.task_uuid == task_id)
        .order_by(TaskEvent.timestamp.asc())
    )
    return [TaskEventSchema.model_validate(e) for e in result.scalars().all()]


@router.post("/{task_id}/revoke")
async def revoke_task(task_id: str, terminate: bool = False):
    """Revoke a task. Set terminate=true to kill the worker process."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None, partial(celery_client.revoke_task, task_id, terminate=terminate)
    )
    return {"status": "revoked", "task_id": task_id, "terminated": terminate}
