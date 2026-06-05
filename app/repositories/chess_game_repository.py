from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc

from app.models.chess_game import ChessGame


class ChessGameRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, game_id: int) -> ChessGame | None:
        return await self.db.get(ChessGame, game_id)

    async def create(self, white_player_id: int, black_player_id: int,
                     time_control: str | None = None) -> ChessGame:
        game = ChessGame(
            white_player_id=white_player_id,
            black_player_id=black_player_id,
            time_control=time_control,
            status="ongoing",
        )
        self.db.add(game)
        await self.db.flush()
        return game

    async def finish(self, game: ChessGame, moves_pgn: str, result: str,
                     winner_id: int | None) -> None:
        game.moves_pgn = moves_pgn
        game.result = result
        game.winner_id = winner_id
        game.status = "finished"
        game.ended_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def get_user_games(self, user_id: int, limit: int = 50) -> list[ChessGame]:
        result = await self.db.execute(
            select(ChessGame)
            .where(or_(ChessGame.white_player_id == user_id,
                       ChessGame.black_player_id == user_id))
            .order_by(desc(ChessGame.started_at))
            .limit(limit)
        )
        return list(result.scalars().all())