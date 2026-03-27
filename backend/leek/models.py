import datetime

from sqlalchemy import DateTime, Float, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from leek.db import Base


class Task(Base):
    __tablename__ = "tasks"

    uuid: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(512), index=True)
    state: Mapped[str] = mapped_column(String(50), index=True, default="PENDING")
    args: Mapped[str | None] = mapped_column(Text)
    kwargs: Mapped[str | None] = mapped_column(Text)
    result: Mapped[str | None] = mapped_column(Text)
    exception: Mapped[str | None] = mapped_column(Text)
    traceback: Mapped[str | None] = mapped_column(Text)
    worker: Mapped[str | None] = mapped_column(String(255), index=True)
    queue: Mapped[str | None] = mapped_column(String(255))
    exchange: Mapped[str | None] = mapped_column(String(255))
    routing_key: Mapped[str | None] = mapped_column(String(255))
    retries: Mapped[int] = mapped_column(default=0)
    eta: Mapped[str | None] = mapped_column(String(255))
    expires: Mapped[str | None] = mapped_column(String(255))
    root_id: Mapped[str | None] = mapped_column(String(255), index=True)
    parent_id: Mapped[str | None] = mapped_column(String(255), index=True)
    runtime: Mapped[float | None] = mapped_column(Float)
    sent_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    succeeded_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    retried_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    last_updated: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_tasks_name_state", "name", "state"),
        Index("ix_tasks_last_updated", "last_updated"),
    )


class Worker(Base):
    __tablename__ = "workers"

    hostname: Mapped[str] = mapped_column(String(512), primary_key=True)
    status: Mapped[str] = mapped_column(String(50), default="online")
    pid: Mapped[int | None] = mapped_column()
    sw_ident: Mapped[str | None] = mapped_column(String(255))
    sw_ver: Mapped[str | None] = mapped_column(String(100))
    sw_sys: Mapped[str | None] = mapped_column(String(100))
    active_tasks: Mapped[int] = mapped_column(default=0)
    processed: Mapped[int] = mapped_column(default=0)
    loadavg: Mapped[str | None] = mapped_column(String(100))
    freq: Mapped[float | None] = mapped_column(Float)
    last_heartbeat: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TaskEvent(Base):
    __tablename__ = "task_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_uuid: Mapped[str] = mapped_column(String(255), index=True)
    event_type: Mapped[str] = mapped_column(String(100))
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), index=True)
    hostname: Mapped[str | None] = mapped_column(String(512))
    data: Mapped[str | None] = mapped_column(Text)  # JSON blob of the raw event

    __table_args__ = (Index("ix_task_events_uuid_ts", "task_uuid", "timestamp"),)
