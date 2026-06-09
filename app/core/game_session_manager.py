from __future__ import annotations

from app.services.game_session_service import GameSessionService
from app.repositories.chess_game_repository import ChessGameRepository


class GameSessionManager:
    def __init__(self):
        self.sessions: dict[int, GameSessionService] = {}

    def get_or_create(self, game_id: int, white_user_id: int, black_user_id: int,
                      game_repo: ChessGameRepository,
                      initial_seconds: int = 300,
                      increment_seconds: int = 0) -> GameSessionService:
        if game_id not in self.sessions:
            self.sessions[game_id] = GameSessionService(
                game_id, white_user_id, black_user_id, game_repo,
                initial_seconds, increment_seconds,
            )
        return self.sessions[game_id]

    def get(self, game_id: int) -> GameSessionService | None:
        return self.sessions.get(game_id)

    def remove(self, game_id: int) -> None:
        self.sessions.pop(game_id, None)

    async def get_or_create(self, game_id: int, white_user_id: int, black_user_id: int,
                            game_repo: ChessGameRepository) -> GameSessionService:
        
        if game_id not in self.sessions:
            session = GameSessionService(game_id, white_user_id, black_user_id, game_repo)
            
            game_data = await game_repo.get_by_id(game_id)
            if game_data and game_data.moves_pgn:
                await session.hydrate_from_history(game_data.moves_pgn)
                
            self.sessions[game_id] = session
            
        return self.sessions[game_id]