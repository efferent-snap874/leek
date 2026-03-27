import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts events to clients."""

    def __init__(self):
        self._connections: dict[WebSocket, dict] = {}  # ws -> subscription filters
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._connections[websocket] = {}

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self._connections.pop(websocket, None)

    async def set_filters(self, websocket: WebSocket, filters: dict):
        async with self._lock:
            if websocket in self._connections:
                self._connections[websocket] = filters

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients whose filters match."""
        async with self._lock:
            connections = list(self._connections.items())

        for ws, filters in connections:
            if self._matches_filters(message, filters):
                try:
                    await ws.send_json(message)
                except Exception:
                    await self.disconnect(ws)

    def _matches_filters(self, message: dict, filters: dict) -> bool:
        if not filters:
            return True

        msg_type = message.get("type", "")
        data = message.get("data", {})

        # Filter by task names
        task_names = filters.get("task_names")
        if task_names and data.get("name") not in task_names:
            return False

        # Filter by states
        states = filters.get("states")
        if states and data.get("state") not in states:
            return False

        return True

    @property
    def active_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if "subscribe" in message:
                    await manager.set_filters(websocket, message["subscribe"])
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
