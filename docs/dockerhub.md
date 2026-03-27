Real-time monitoring and administration for Celery task queues.

Leek connects to your existing Celery broker and gives you a live dashboard, task explorer, worker monitoring, and task-level control — all from a single Docker container. No code changes, no agents, no plugins required.

## Quick Start

```bash
docker run -d \
  -e CELERY_BROKER_URL=redis://your-redis-host:6379/0 \
  -p 8585:8585 \
  wmbitfarm/leek
```

Open http://localhost:8585. That's it.

**One requirement:** your Celery workers must have events enabled (`celery -A app worker -E` or `worker_send_task_events = True`).

## Features

- **Real-time dashboard** — live task counts, stacked throughput chart (color-coded by state), worker status
- **Task explorer** — search, filter, sort all tasks with live state updates over WebSocket
- **Task detail** — full args/kwargs, results, exception/traceback, state timeline, revoke/terminate
- **Task type stats** — per-type counts, failure rate, avg and p95 runtime, recent tasks per type
- **Worker monitoring** — online/offline status, heartbeat tracking, ping all workers
- **Live event stream** — filterable real-time feed of all Celery events
- **Broker-agnostic** — works with Redis, RabbitMQ, SQS, or any Celery-supported broker

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CELERY_BROKER_URL` | Yes | — | Broker connection string (redis://, amqp://, sqs://) |
| `DATABASE_URL` | No | SQLite | Set to a PostgreSQL URL for high-throughput deployments |
| `LEEK_RETENTION_DAYS` | No | 7 | Days to keep task history |
| `LEEK_PORT` | No | 8585 | Port inside the container |

## Persist Data

Mount a volume to keep task history across container restarts:

```bash
docker run -d \
  -e CELERY_BROKER_URL=redis://redis:6379/0 \
  -p 8585:8585 \
  -v leek-data:/app \
  wmbitfarm/leek
```

## How It Works

Leek uses Celery's built-in event protocol — no direct broker inspection needed. It creates a standalone Celery app instance, connects to your broker, and listens for task lifecycle events and worker heartbeats. Events are persisted to SQLite (or PostgreSQL) and streamed to the browser over WebSocket.

Zero coupling to your application code. Zero config beyond a broker URL.

## Links

- **Source:** https://github.com/wmbitfarm/leek
- **License:** MIT
