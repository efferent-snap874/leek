from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from leek.db import get_session
from leek.event_listener import event_listener
from leek.models import Task, Worker
from leek.schemas import DashboardStats, TaskTypeStats

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats(session: AsyncSession = Depends(get_session)):
    now = datetime.now(timezone.utc)
    one_minute_ago = now - timedelta(minutes=1)

    # Task counts by state
    state_counts = await session.execute(
        select(Task.state, func.count()).group_by(Task.state)
    )
    counts = dict(state_counts.all())

    total = sum(counts.values())
    active = counts.get("STARTED", 0)
    succeeded = counts.get("SUCCESS", 0)
    failed = counts.get("FAILURE", 0)

    # Worker counts
    worker_counts = await session.execute(
        select(Worker.status, func.count()).group_by(Worker.status)
    )
    w_counts = dict(worker_counts.all())
    workers_online = w_counts.get("online", 0)
    workers_offline = w_counts.get("offline", 0)

    # Tasks per minute (tasks that succeeded in the last minute)
    tpm_result = await session.execute(
        select(func.count())
        .select_from(Task)
        .where(Task.succeeded_at >= one_minute_ago)
    )
    tasks_per_minute = float(tpm_result.scalar() or 0)

    return DashboardStats(
        total_tasks=total,
        active_tasks=active,
        succeeded_tasks=succeeded,
        failed_tasks=failed,
        workers_online=workers_online,
        workers_offline=workers_offline,
        tasks_per_minute=tasks_per_minute,
        events_received=event_listener.events_received,
    )


@router.get("/task-types", response_model=list[TaskTypeStats])
async def task_type_stats(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(
            Task.name,
            func.count().label("total_count"),
            func.sum(case((Task.state == "SUCCESS", 1), else_=0)).label("success_count"),
            func.sum(case((Task.state == "FAILURE", 1), else_=0)).label("failure_count"),
            func.avg(Task.runtime).label("avg_runtime"),
        )
        .where(Task.name.isnot(None))
        .group_by(Task.name)
        .order_by(func.count().desc())
    )

    stats = []
    for row in result.all():
        total = row.total_count
        failures = row.failure_count or 0
        stats.append(
            TaskTypeStats(
                name=row.name,
                total_count=total,
                success_count=row.success_count or 0,
                failure_count=failures,
                failure_rate=failures / total if total > 0 else 0.0,
                avg_runtime=round(row.avg_runtime, 3) if row.avg_runtime else None,
                p95_runtime=None,  # Computed below if needed
            )
        )

    # Compute p95 runtime per task type (separate query for SQLite compat)
    for stat in stats:
        p95_result = await session.execute(
            select(Task.runtime)
            .where(Task.name == stat.name, Task.runtime.isnot(None))
            .order_by(Task.runtime.asc())
        )
        runtimes = [r[0] for r in p95_result.all()]
        if runtimes:
            idx = int(len(runtimes) * 0.95)
            stat.p95_runtime = round(runtimes[min(idx, len(runtimes) - 1)], 3)

    return stats


@router.get("/throughput")
async def throughput(
    minutes: int = 60,
    session: AsyncSession = Depends(get_session),
):
    """Task throughput over time, bucketed by minute and state."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    result = await session.execute(
        select(
            func.strftime("%Y-%m-%dT%H:%M", Task.last_updated).label("minute"),
            Task.state,
            func.count().label("count"),
        )
        .where(Task.last_updated >= cutoff)
        .group_by(text("minute"), Task.state)
        .order_by(text("minute"))
    )

    # Group by minute: { "2026-03-27T03:41": { "SUCCESS": 5, "FAILURE": 1, ... } }
    minutes_map = {}
    for row in result.all():
        if row.minute not in minutes_map:
            minutes_map[row.minute] = {}
        minutes_map[row.minute][row.state] = row.count

    return [
        {"minute": minute, "states": states}
        for minute, states in sorted(minutes_map.items())
    ]
