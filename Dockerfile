# Stage 1: Build frontend
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim
WORKDIR /app

# Copy backend code and install
COPY backend/ ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

EXPOSE 8585

ENV LEEK_HOST=0.0.0.0
ENV LEEK_PORT=8585
ENV PYTHONPATH=/app/backend

CMD ["python", "-m", "leek.main"]
