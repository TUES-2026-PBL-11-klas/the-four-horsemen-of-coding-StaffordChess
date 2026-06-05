import uuid
import random
from fastapi import WebSocket
from app.schemas.lobby_dto import GameConfig, LobbyChallenge
from app.repositories.chess_game_repository import ChessGameRepository

class LobbyService:
    def __init__(self):
        self.waiting_games: dict[str, LobbyChallenge] = {}
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

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
            color_preference=config.color_preference
        )
        self.waiting_games[challenge.id] = challenge
        
        await self.broadcast({"type": "NEW_CHALLENGE", "challenge": challenge.model_dump()})
        return challenge

    async def remove_from_lobby(self, challenge_id: str):
        if challenge_id in self.waiting_games:
            del self.waiting_games[challenge_id]
            await self.broadcast({"type": "REMOVE_CHALLENGE", "challenge_id": challenge_id})

    async def match_players(self, challenge_id: str, opponent, game_repo: ChessGameRepository):
        if challenge_id not in self.waiting_games:
            raise ValueError("Challenge not found or already accepted")
        
        challenge = self.waiting_games[challenge_id]
        if challenge.host_id == opponent.id:
            raise ValueError("You cannot accept your own challenge")

        host_color = challenge.color_preference
        if host_color == "random":
            host_color = random.choice(["white", "black"])

        if host_color == "white":
            white_id = challenge.host_id
            black_id = opponent.id
        else:
            white_id = opponent.id
            black_id = challenge.host_id

        game = await game_repo.create(white_id, black_id, challenge.time_control)
        
        await self.remove_from_lobby(challenge_id)
        
        await self.broadcast({
            "type": "MATCH_STARTED",
            "challenge_id": challenge_id,
            "game_id": game.id
        })

        return game