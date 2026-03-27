from celery import Celery

from leek.config import settings

# Standalone Celery app — only used for events, inspect, and control.
# Does NOT register any tasks or run any workers.
celery_app = Celery("leek", broker=settings.celery_broker_url)
celery_app.config_from_object(
    {
        "worker_enable_remote_control": True,
        "task_send_sent_event": True,
    }
)


def inspect_workers() -> dict:
    """Query all workers for their current state."""
    inspector = celery_app.control.inspect(timeout=3.0)
    return {
        "active": inspector.active() or {},
        "reserved": inspector.reserved() or {},
        "scheduled": inspector.scheduled() or {},
        "registered": inspector.registered() or {},
        "stats": inspector.stats() or {},
    }


def inspect_active() -> dict:
    inspector = celery_app.control.inspect(timeout=3.0)
    return inspector.active() or {}


def revoke_task(task_id: str, terminate: bool = False, signal: str = "SIGTERM") -> None:
    """Revoke (and optionally terminate) a task."""
    celery_app.control.revoke(task_id, terminate=terminate, signal=signal)


def ping_workers() -> dict:
    """Ping all workers to check connectivity."""
    return celery_app.control.ping(timeout=2.0) or []
