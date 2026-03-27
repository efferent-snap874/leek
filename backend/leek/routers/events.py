from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from leek.db import get_session
from leek.models import TaskEvent
from leek.schemas import TaskEventSchema

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=list[TaskEventSchema])
async def list_events(
    event_type: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
):
    """Get recent events, newest first."""
    query = select(TaskEvent).order_by(TaskEvent.timestamp.desc()).limit(limit)

    if event_type:
        query = query.where(TaskEvent.event_type == event_type)

    result = await session.execute(query)
    return [TaskEventSchema.model_validate(e) for e in result.scalars().all()]
