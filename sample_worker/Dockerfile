FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir celery[redis]
COPY sample_worker/tasks.py sample_worker/generate_tasks.py ./
