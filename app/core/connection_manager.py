from __future__ import annotations

from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        self.connections: dict[int, list[WebSocket]] = {}

    async def connect(self, game_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.setdefault(game_id, []).append(websocket)

    def disconnect(self, game_id: int, websocket: WebSocket) -> None:
        if game_id in self.connections:
            if websocket in self.connections[game_id]:
                self.connections[game_id].remove(websocket)
            if not self.connections[game_id]:
                del self.connections[game_id]

    async def broadcast(self, game_id: int, message: dict) -> None:
        for connection in self.connections.get(game_id, []):
            try:
                await connection.send_json(message)
            except Exception:
                pass