import json
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        self._connections[user_id].remove(websocket)
        if not self._connections[user_id]:
            del self._connections[user_id]

    async def broadcast(self, user_id: str, data: dict) -> None:
        dead = []
        for ws in self._connections.get(user_id, []):
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections[user_id].remove(ws)


manager = ConnectionManager()
