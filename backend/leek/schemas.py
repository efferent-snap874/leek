import datetime

from pydantic import BaseModel


class TaskSummary(BaseModel):
    uuid: str
    name: str | None = None
    state: str
    worker: str | None = None
    runtime: float | None = None
    started_at: datetime.datetime | None = None
    last_updated: datetime.datetime

    model_config = {"from_attributes": True}


class TaskDetail(BaseModel):
    uuid: str
    name: str | None = None
    state: str
    args: str | None = None
    kwargs: str | None = None
    result: str | None = None
    exception: str | None = None
    traceback: str | None = None
    worker: str | None = None
    queue: str | None = None
    exchange: str | None = None
    routing_key: str | None = None
    retries: int = 0
    eta: str | None = None
    expires: str | None = None
    root_id: str | None = None
    parent_id: str | None = None
    runtime: float | None = None
    sent_at: datetime.datetime | None = None
    received_at: datetime.datetime | None = None
    started_at: datetime.datetime | None = None
    succeeded_at: datetime.datetime | None = None
    failed_at: datetime.datetime | None = None
    revoked_at: datetime.datetime | None = None
    retried_at: datetime.datetime | None = None
    rejected_at: datetime.datetime | None = None
    last_updated: datetime.datetime

    model_config = {"from_attributes": True}


class TaskEventSchema(BaseModel):
    id: int
    task_uuid: str
    event_type: str
    timestamp: datetime.datetime
    hostname: str | None = None
    data: str | None = None

    model_config = {"from_attributes": True}


class WorkerSchema(BaseModel):
    hostname: str
    status: str
    pid: int | None = None
    sw_ident: str | None = None
    sw_ver: str | None = None
    sw_sys: str | None = None
    active_tasks: int = 0
    processed: int = 0
    loadavg: str | None = None
    freq: float | None = None
    last_heartbeat: datetime.datetime | None = None
    first_seen: datetime.datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_tasks: int
    active_tasks: int
    succeeded_tasks: int
    failed_tasks: int
    workers_online: int
    workers_offline: int
    tasks_per_minute: float
    events_received: bool


class TaskTypeStats(BaseModel):
    name: str
    total_count: int
    success_count: int
    failure_count: int
    failure_rate: float
    avg_runtime: float | None = None
    p95_runtime: float | None = None


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
