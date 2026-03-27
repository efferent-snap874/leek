import asyncio
from functools import partial

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from leek import celery_client
from leek.db import get_session
from leek.models import Worker
from leek.schemas import WorkerSchema

router = APIRouter(prefix="/api/workers", tags=["workers"])


@router.get("", response_model=list[WorkerSchema])
async def list_workers(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Worker).order_by(Worker.hostname))
    return [WorkerSchema.model_validate(w) for w in result.scalars().all()]


@router.get("/{hostname}", response_model=WorkerSchema)
async def get_worker(hostname: str, session: AsyncSession = Depends(get_session)):
    worker = await session.get(Worker, hostname)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return WorkerSchema.model_validate(worker)


@router.get("/{hostname}/tasks")
async def get_worker_active_tasks(hostname: str):
    """Get active tasks for a worker via Celery inspect API."""
    loop = asyncio.get_event_loop()
    active = await loop.run_in_executor(None, celery_client.inspect_active)
    return active.get(hostname, [])


@router.post("/ping")
async def ping_workers():
    """Ping all workers to check connectivity."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, celery_client.ping_workers)
    return result
