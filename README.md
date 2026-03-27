# Leek

Real-time monitoring and administration for [Celery](https://docs.celeryq.dev/) task queues.

Leek connects to your existing Celery broker and gives you a live dashboard, task explorer, worker monitoring, and task-level control — all from a single Docker container. No code changes, no agents, no plugins required.

![Dashboard](docs/screenshots/dashboard.png)

## Features

- **Real-time dashboard** — live task counts, throughput chart (stacked by state), worker status, recent activity
- **Task explorer** — searchable, filterable, sortable table with live state updates via WebSocket
- **Task detail** — full args/kwargs, result, exception/traceback, state timeline, retry chain, revoke/terminate
- **Task type overview** — per-type stats (count, failure rate, avg/p95 runtime) with card and list views, 5 most recent tasks per type
- **Worker monitoring** — online/offline status, heartbeat tracking, active task counts, worker metadata
- **Live event stream** — filterable real-time feed of all Celery events
- **Broker-agnostic** — works with Redis, RabbitMQ, Amazon SQS, or any Celery-supported broker
- **Zero config** — one environment variable to get started

## Quick Start

```bash
docker run -d \
  -e CELERY_BROKER_URL=redis://your-redis-host:6379/0 \
  -p 8585:8585 \
  --name leek \
  leek/leek
```

Open [http://localhost:8585](http://localhost:8585).

That's it. Leek connects to your broker, listens for Celery events, and starts populating the dashboard.

### Requirements

Your Celery workers **must have events enabled**. Leek uses Celery's event protocol — without events, there's nothing to monitor.

Enable events by starting workers with the `-E` flag:

```bash
celery -A your_app worker -E
```

Or set it in your Celery config:

```python
# celeryconfig.py or settings.py
worker_send_task_events = True
task_send_sent_event = True  # optional: also capture the "sent" event
```

If events aren't enabled, Leek will show a warning banner on the dashboard with setup instructions.

> **Note:** Enabling events has negligible performance impact on your workers. The events are small messages sent over your existing broker connection.

## Configuration

Leek is configured entirely through environment variables.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CELERY_BROKER_URL` | **Yes** | — | Your Celery broker URL. Examples below. |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///leek.db` | Database URL. SQLite (default) or PostgreSQL. |
| `LEEK_RETENTION_DAYS` | No | `7` | Number of days to keep task history before cleanup. |
| `LEEK_PORT` | No | `8585` | Port Leek listens on inside the container. |

### Broker URL Examples

```bash
# Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://:password@redis-host:6379/0
CELERY_BROKER_URL=rediss://user:password@redis-host:6380/0  # TLS

# RabbitMQ
CELERY_BROKER_URL=amqp://user:password@rabbitmq-host:5672/vhost
CELERY_BROKER_URL=amqps://user:password@rabbitmq-host:5671/vhost  # TLS

# Amazon SQS
CELERY_BROKER_URL=sqs://aws_access_key:aws_secret_key@
```

### Persisting Data

By default, Leek stores task history in a SQLite database inside the container at `/app/leek.db`. To persist data across container restarts, mount a volume:

```bash
docker run -d \
  -e CELERY_BROKER_URL=redis://redis:6379/0 \
  -p 8585:8585 \
  -v leek-data:/app \
  leek/leek
```

### Using PostgreSQL

For high-throughput deployments or running multiple Leek instances, switch to PostgreSQL:

```bash
docker run -d \
  -e CELERY_BROKER_URL=redis://redis:6379/0 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/leek \
  -p 8585:8585 \
  leek/leek
```

Install the `asyncpg` driver — it's included in the Docker image. If running outside Docker, install the `postgres` extra: `pip install leek[postgres]`.

### Docker Compose

```yaml
services:
  leek:
    image: leek/leek
    ports:
      - "8585:8585"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    volumes:
      - leek-data:/app
    restart: unless-stopped

volumes:
  leek-data:
```

## Screenshots

### Dashboard

The dashboard shows live stats, a stacked throughput chart (color-coded by task state), and a recent activity feed. Stats refresh every 5 seconds. The throughput chart always shows the last 60 minutes.

![Dashboard](docs/screenshots/dashboard.png)

### Task Explorer

Browse all tasks with search, state/type filters, and sorting. Task states update in real-time via WebSocket — you'll see badges change from STARTED to SUCCESS without refreshing.

![Task Explorer](docs/screenshots/task-explorer.png)

### Task Detail

Drill into any task to see its full arguments, result or exception with traceback, state timeline, and event history. Running tasks can be revoked or terminated directly from this view.

![Task Detail](docs/screenshots/task-detail.png)

### Task Types

See aggregate statistics for each registered task type — total count, success/failure counts, failure rate, average and p95 runtime. The card view shows the 5 most recent tasks per type, updating live. Toggle between card and list views. Filter by task name.

![Task Types](docs/screenshots/task-types-cards.png)

### Workers

Monitor worker status with live heartbeat tracking. See each worker's active task count, total processed count, software version, and system info. Ping all workers to verify connectivity.

![Workers](docs/screenshots/workers.png)

### Event Stream

A live, filterable feed of every Celery event. Filter by event type (task-sent, task-failed, worker-online, etc.). Load historical events from the database.

![Event Stream](docs/screenshots/event-stream.png)

## How It Works

Leek uses Celery's built-in APIs — no direct broker access is needed beyond the initial connection:

1. **Events** — Leek runs a persistent [EventReceiver](https://docs.celeryq.dev/en/stable/userguide/monitoring.html#events) that captures task lifecycle events (sent, received, started, succeeded, failed, retried, revoked) and worker heartbeats.
2. **Inspect** — On-demand queries to workers for active/reserved/scheduled tasks, registered task types, and worker stats.
3. **Control** — Task revocation and termination via Celery's broadcast control API.

Events are persisted to a local database (SQLite or PostgreSQL) for historical queries. Real-time updates are pushed to the browser over WebSocket.

```
Your Celery Workers                    Leek Container
┌──────────────┐                  ┌─────────────────────┐
│  Worker 1    │──events──┐       │  FastAPI + uvicorn   │
│  Worker 2    │──events──┤       │                      │
│  Worker N    │──events──┼──►────│  Event Listener      │
└──────────────┘          │       │    ↓                  │
                     ┌────┴───┐   │  SQLite/Postgres      │
                     │ Broker │   │    ↓                  │
                     └────────┘   │  WebSocket → Browser  │
                                  └─────────────────────┘
```

### Architecture Notes

- **Single-writer database pattern** — The event listener is the sole writer to the database. API endpoints only read. This means SQLite in WAL mode handles the workload without write contention.
- **Background thread** — Celery's event system is synchronous (kombu-based), so it runs in a background thread. Events are passed to the async FastAPI process via an `asyncio.Queue`.
- **Data retention** — Old task records are automatically cleaned up every hour based on `LEEK_RETENTION_DAYS`. Default is 7 days.

## Task Control

Leek supports revoking and terminating running tasks from the Task Detail view.

- **Revoke** — Tells the worker to discard the task if it hasn't started yet. If the task is already running, it will complete normally.
- **Terminate** — Sends a signal (SIGTERM) to the worker process executing the task. The task will be killed.

These operations use Celery's [control.revoke](https://docs.celeryq.dev/en/stable/userguide/workers.html#revoking-tasks) API. They work across all broker types.

> **Warning:** Terminate kills the worker process handling the task. The worker pool will spawn a replacement, but any in-progress work in that process is lost. Use with care.

## What Leek Doesn't Do

- **Queue depth** — Celery's API doesn't expose queue sizes. Leek shows reserved/scheduled counts per worker, but not raw queue depth. This would require broker-specific integrations (planned for a future release).
- **Authentication** — Leek is currently single-user with no auth. It's intended for internal/development use. Run it behind a VPN or reverse proxy with auth if exposing to a network.
- **External notifications** — No Slack, email, or PagerDuty integration. Alerts are in-UI only.
- **Result backend** — Leek captures results included in Celery events (enable with `result_extended = True` in your Celery config), but does not connect to a separate result backend.

## Troubleshooting

### "No events received" warning

Leek is connected to the broker but no workers are sending events. Check:

1. Workers are started with `-E`: `celery -A app worker -E`
2. Or config includes `worker_send_task_events = True`
3. Workers are connected to the **same broker** as Leek
4. No firewall blocking the broker connection from the Leek container

### Tasks show as PENDING but never progress

This usually means `task_send_sent_event = True` is set (so Leek sees the send event) but the worker isn't sending lifecycle events. Enable `-E` on your workers.

### High memory usage

Leek keeps recent tasks in memory for WebSocket broadcasting (capped at 5,000 entries). If you're running a very high-throughput system, consider:

- Reducing `LEEK_RETENTION_DAYS`
- Switching to PostgreSQL for better query performance on large datasets

### Container can't connect to broker

If using Docker, make sure the broker URL uses the correct hostname. `localhost` inside a container refers to the container itself, not your host machine. Use the Docker service name or host IP:

```bash
# Wrong (from inside a container)
CELERY_BROKER_URL=redis://localhost:6379/0

# Right (Docker Compose service name)
CELERY_BROKER_URL=redis://redis:6379/0

# Right (host machine, Docker for Mac/Windows)
CELERY_BROKER_URL=redis://host.docker.internal:6379/0
```

## Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose

### Running locally with Docker Compose

The repo includes a full dev setup with Redis, a sample Celery worker, and a task generator:

```bash
git clone https://github.com/your-org/leek.git
cd leek
docker compose up --build
```

This starts:
- **Redis** on port 6379
- **Sample Celery worker** with demo tasks (add, multiply, slow_task, flaky_task)
- **Task generator** that submits random tasks every 0.5–3 seconds
- **Leek backend** on port 8585
- **Vite dev server** on port 3000 (frontend with hot reload)

Open [http://localhost:3000](http://localhost:3000) for development (Vite proxies API/WebSocket calls to the backend). Backend code is volume-mounted — restart the `leek` container to pick up Python changes.

### Running without Docker

```bash
# Backend
cd backend
pip install -e ".[dev]"
CELERY_BROKER_URL=redis://localhost:6379/0 python -m leek.main

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | [FastAPI](https://fastapi.tiangolo.com/) + [uvicorn](https://www.uvicorn.org/) |
| Database | SQLite (WAL mode) / PostgreSQL |
| ORM | [SQLAlchemy](https://www.sqlalchemy.org/) async |
| Celery integration | [celery](https://docs.celeryq.dev/) events, inspect, control APIs |
| Frontend | [Vue 3](https://vuejs.org/) (Composition API) |
| Styling | [Tailwind CSS](https://tailwindcss.com/) + [DaisyUI](https://daisyui.com/) |
| Build | [Vite](https://vitejs.dev/) |
| Container | Docker (multi-stage build) |

## License

MIT — see [LICENSE](LICENSE).
