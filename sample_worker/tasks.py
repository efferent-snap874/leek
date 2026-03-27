import os
import random
import time

from celery import Celery

app = Celery("demo", broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"))
app.conf.task_send_sent_event = True
app.conf.worker_send_task_events = True


@app.task
def add(x, y):
    time.sleep(random.uniform(0.1, 0.5))
    return x + y


@app.task
def multiply(x, y):
    time.sleep(random.uniform(0.2, 1.0))
    return x * y


@app.task
def slow_task(duration=5):
    time.sleep(duration)
    return f"Slept for {duration}s"


@app.task
def flaky_task():
    time.sleep(random.uniform(0.1, 0.3))
    if random.random() < 0.3:
        raise ValueError("Random failure!")
    return "ok"


@app.task
def chain_parent():
    result = chain_child.delay()
    return f"Spawned child: {result.id}"


@app.task
def chain_child():
    time.sleep(random.uniform(0.1, 0.5))
    return "child done"
