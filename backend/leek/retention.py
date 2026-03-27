import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from leek.config import settings
from leek.db import async_session
from leek.models import Task, TaskEvent

logger = logging.getLogger(__name__)


async def cleanup_old_records():
    """Periodically delete task records older than the retention period."""
    while True:
        await asyncio.sleep(3600)  # Run every hour
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=settings.retention_days)
            async with async_session() as session:
                # Delete old task events first
                result = await session.execute(
                    delete(TaskEvent).where(TaskEvent.timestamp < cutoff)
                )
                events_deleted = result.rowcount

                # Delete old tasks
                result = await session.execute(
                    delete(Task).where(Task.last_updated < cutoff)
                )
                tasks_deleted = result.rowcount

                await session.commit()

                if events_deleted or tasks_deleted:
                    logger.info(
                        "Retention cleanup: deleted %d events and %d tasks older than %d days",
                        events_deleted,
                        tasks_deleted,
                        settings.retention_days,
                    )
        except Exception:
            logger.exception("Error during retention cleanup")
