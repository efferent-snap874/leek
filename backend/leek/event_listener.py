import asyncio
import json
import logging
import threading
from datetime import datetime, timezone

from sqlalchemy import select

from leek.celery_client import celery_app
from leek.db import async_session
from leek.models import Task, TaskEvent, Worker
from leek.ws import manager

logger = logging.getLogger(__name__)

# Maps Celery event types to task states
EVENT_STATE_MAP = {
    "task-sent": "PENDING",
    "task-received": "RECEIVED",
    "task-started": "STARTED",
    "task-succeeded": "SUCCESS",
    "task-failed": "FAILURE",
    "task-retried": "RETRY",
    "task-revoked": "REVOKED",
    "task-rejected": "REJECTED",
}

# Maps event types to timestamp fields on the Task model
EVENT_TIMESTAMP_MAP = {
    "task-sent": "sent_at",
    "task-received": "received_at",
    "task-started": "started_at",
    "task-succeeded": "succeeded_at",
    "task-failed": "failed_at",
    "task-revoked": "revoked_at",
    "task-retried": "retried_at",
    "task-rejected": "rejected_at",
}


class EventListener:
    """Listens for Celery events in a background thread, pushes them to an asyncio queue."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self.events_received = False

    def start(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _listen(self):
        """Run in background thread — receives Celery events via kombu."""
        logger.info("Starting Celery event listener on broker: %s", celery_app.conf.broker_url)

        def on_event(event):
            self.events_received = True
            asyncio.run_coroutine_threadsafe(self._queue.put(event), self._loop)

        with celery_app.connection() as conn:
            recv = celery_app.events.Receiver(
                conn,
                handlers={"*": on_event},
            )
            try:
                recv.capture(limit=None, timeout=None, wakeup=True)
            except Exception:
                if not self._stop_event.is_set():
                    logger.exception("Event listener crashed, will restart")
                    # Brief pause before restart
                    self._stop_event.wait(2)
                    if not self._stop_event.is_set():
                        self._listen()

    async def process_events(self):
        """Async loop that drains the queue — runs as an asyncio task."""
        while True:
            event = await self._queue.get()
            try:
                await self._handle_event(event)
            except Exception:
                logger.exception("Error processing event: %s", event)

    async def _handle_event(self, event: dict):
        event_type = event.get("type", "")
        timestamp = datetime.fromtimestamp(event.get("timestamp", 0), tz=timezone.utc)
        hostname = event.get("hostname")

        if event_type.startswith("task-"):
            await self._handle_task_event(event, event_type, timestamp, hostname)
        elif event_type.startswith("worker-"):
            await self._handle_worker_event(event, event_type, timestamp, hostname)

    async def _handle_task_event(
        self, event: dict, event_type: str, timestamp: datetime, hostname: str | None
    ):
        task_uuid = event.get("uuid")
        if not task_uuid:
            return

        state = EVENT_STATE_MAP.get(event_type)
        timestamp_field = EVENT_TIMESTAMP_MAP.get(event_type)

        async with async_session() as session:
            # Upsert the task record
            task = await session.get(Task, task_uuid)
            if task is None:
                task = Task(uuid=task_uuid)
                session.add(task)

            if state:
                task.state = state
            if hostname:
                task.worker = hostname
            if timestamp_field:
                setattr(task, timestamp_field, timestamp)

            # Extract fields from event
            for field in ("name", "args", "kwargs", "result", "exception", "traceback",
                          "queue", "exchange", "routing_key", "eta", "expires",
                          "root_id", "parent_id", "retries"):
                if field in event:
                    value = event[field]
                    if field in ("args", "kwargs") and not isinstance(value, str):
                        value = json.dumps(value)
                    setattr(task, field, value)

            if "runtime" in event:
                task.runtime = event["runtime"]

            # Record the event
            task_event = TaskEvent(
                task_uuid=task_uuid,
                event_type=event_type,
                timestamp=timestamp,
                hostname=hostname,
                data=json.dumps(event, default=str),
            )
            session.add(task_event)
            await session.commit()

            # Broadcast to WebSocket clients
            ws_message = {
                "type": "task_update",
                "data": {
                    "uuid": task_uuid,
                    "name": task.name,
                    "state": task.state,
                    "worker": task.worker,
                    "runtime": task.runtime,
                    "event_type": event_type,
                    "timestamp": timestamp.isoformat(),
                    "args": task.args,
                    "kwargs": task.kwargs,
                    "exception": task.exception,
                },
            }
            await manager.broadcast(ws_message)

    async def _handle_worker_event(
        self, event: dict, event_type: str, timestamp: datetime, hostname: str | None
    ):
        if not hostname:
            return

        async with async_session() as session:
            worker = await session.get(Worker, hostname)
            if worker is None:
                worker = Worker(hostname=hostname)
                session.add(worker)

            if event_type == "worker-online":
                worker.status = "online"
            elif event_type == "worker-offline":
                worker.status = "offline"
            elif event_type == "worker-heartbeat":
                worker.status = "online"
                worker.last_heartbeat = timestamp
                if "active" in event:
                    worker.active_tasks = event["active"]
                if "processed" in event:
                    worker.processed = event["processed"]
                if "loadavg" in event:
                    worker.loadavg = json.dumps(event["loadavg"])
                if "freq" in event:
                    worker.freq = event["freq"]
                if "sw_ident" in event:
                    worker.sw_ident = event["sw_ident"]
                if "sw_ver" in event:
                    worker.sw_ver = event["sw_ver"]
                if "sw_sys" in event:
                    worker.sw_sys = event["sw_sys"]
                if "pid" in event:
                    worker.pid = event["pid"]

            await session.commit()

            ws_message = {
                "type": "worker_update",
                "data": {
                    "hostname": hostname,
                    "status": worker.status,
                    "event_type": event_type,
                    "timestamp": timestamp.isoformat(),
                    "active_tasks": worker.active_tasks,
                    "processed": worker.processed,
                },
            }
            await manager.broadcast(ws_message)


# Singleton
event_listener = EventListener()
