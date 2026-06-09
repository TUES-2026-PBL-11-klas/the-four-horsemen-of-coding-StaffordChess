import uuid
import random
import asyncio

from fastapi import WebSocket

from app.schemas.lobby_dto import GameConfig, LobbyChallenge
from app.repositories.chess_game_repository import ChessGameRepository


class LobbyService:
    def __init__(self):
        self.waiting_games: dict[str, LobbyChallenge] = {}
        self.active_connections: list[WebSocket] = []
        self._connection_users: dict[WebSocket, int] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections.append(websocket)
        self._connection_users[websocket] = user_id

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        user_id = self._connection_users.pop(websocket, None)
        if user_id is None:
            return

        if user_id in self._connection_users.values():
            return

        stale = [cid for cid, ch in self.waiting_games.items() if ch.host_id == user_id]
        for cid in stale:
            await self.remove_from_lobby(cid)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    def get_active_games(self) -> list[LobbyChallenge]:
        return list(self.waiting_games.values())

    async def add_to_lobby(self, user, config: GameConfig) -> LobbyChallenge:
        challenge = LobbyChallenge(
            id=str(uuid.uuid4()),
            host_id=user.id,
            host_username=user.username,
            host_rating=user.current_rating,
            time_control=config.time_control,
            color_preference=config.color_preference,
        )
        self.waiting_games[challenge.id] = challenge

        await self.broadcast({"type": "NEW_CHALLENGE", "challenge": challenge.model_dump()})
        return challenge

    async def remove_from_lobby(self, challenge_id: str):
        if challenge_id in self.waiting_games:
            del self.waiting_games[challenge_id]
            await self.broadcast({"type": "REMOVE_CHALLENGE", "challenge_id": challenge_id})

    async def match_players(self, challenge_id: str, opponent, game_repo: ChessGameRepository):
        async with self._lock:
            challenge = self.waiting_games.get(challenge_id)
            if challenge is None:
                raise ValueError("Challenge not found or already accepted")
            if challenge.host_id == opponent.id:
                raise ValueError("You cannot accept your own challenge")
            del self.waiting_games[challenge_id]

        host_color = challenge.color_preference
        if host_color == "random":
            host_color = random.choice(["white", "black"])

        if host_color == "white":
            white_id, black_id = challenge.host_id, opponent.id
        else:
            white_id, black_id = opponent.id, challenge.host_id

        game = await game_repo.create(white_id, black_id, challenge.time_control)

        await self.broadcast({"type": "REMOVE_CHALLENGE", "challenge_id": challenge_id})
        await self.broadcast({
            "type": "MATCH_STARTED",
            "challenge_id": challenge_id,
            "game_id": game.id,
        })
        return game

    async def cancel_challenge(self, challenge_id: str, user_id: int):
        async with self._lock:
            challenge = self.waiting_games.get(challenge_id)
            if challenge is None:
                raise ValueError("Challenge not found")
            if challenge.host_id != user_id:
                raise PermissionError("You can only cancel your own challenges")
            del self.waiting_games[challenge_id]

        await self.broadcast({"type": "REMOVE_CHALLENGE", "challenge_id": challenge_id})