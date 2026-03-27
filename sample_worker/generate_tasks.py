"""Generates demo tasks at random intervals to populate Leek with data."""

import os
import random
import time

from celery import Celery

app = Celery("demo", broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"))


def main():
    print("Starting task generator...")
    time.sleep(5)  # Wait for worker to be ready

    while True:
        choice = random.choice(["add", "multiply", "slow", "flaky", "chain"])

        if choice == "add":
            app.send_task("tasks.add", args=[random.randint(1, 100), random.randint(1, 100)])
        elif choice == "multiply":
            app.send_task("tasks.multiply", args=[random.randint(1, 50), random.randint(1, 50)])
        elif choice == "slow":
            app.send_task("tasks.slow_task", kwargs={"duration": random.randint(2, 8)})
        elif choice == "flaky":
            app.send_task("tasks.flaky_task")
        elif choice == "chain":
            app.send_task("tasks.chain_parent")

        time.sleep(random.uniform(0.5, 3.0))


if __name__ == "__main__":
    main()
