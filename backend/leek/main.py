import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from leek.config import settings
from leek.db import init_db
from leek.event_listener import event_listener
from leek.retention import cleanup_old_records
from leek.routers import events, stats, tasks, workers
from leek.ws import websocket_endpoint

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    await init_db()

    logger.info("Starting Celery event listener...")
    loop = asyncio.get_event_loop()
    event_listener.start(loop)

    # Start the async event processor and retention cleanup
    processor_task = asyncio.create_task(event_listener.process_events())
    retention_task = asyncio.create_task(cleanup_old_records())

    logger.info("Leek is ready — listening for Celery events on %s", settings.celery_broker_url)

    yield

    # Shutdown
    logger.info("Shutting down...")
    event_listener.stop()
    processor_task.cancel()
    retention_task.cancel()


app = FastAPI(
    title="Leek",
    description="Real-time Celery monitoring and administration",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — permissive for dev, tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(tasks.router)
app.include_router(workers.router)
app.include_router(stats.router)
app.include_router(events.router)

# WebSocket
app.add_api_websocket_route("/ws", websocket_endpoint)


# Health check
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "events_received": event_listener.events_received,
        "broker_url": settings.celery_broker_url,
    }


# Serve frontend static files (built Vue app)
STATIC_DIR = Path(__file__).parent.parent.parent / "frontend" / "dist"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")


def main():
    import uvicorn

    uvicorn.run(
        "leek.main:app",
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
