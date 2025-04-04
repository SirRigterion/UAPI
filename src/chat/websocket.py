from fastapi import WebSocket
from redis.asyncio import Redis
from src.core.config import settings

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.redis = Redis.from_url(settings.REDIS_URL)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()