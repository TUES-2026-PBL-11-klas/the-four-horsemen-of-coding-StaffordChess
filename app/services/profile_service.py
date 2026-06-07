from fastapi import HTTPException

from app.repositories.user_repository import UserRepository
from app.repositories.chess_game_repository import ChessGameRepository
from app.repositories.rating_history_repository import RatingHistoryRepository
from app.schemas.profile_dto import ProfileResponse, GameHistoryItem, RatingPoint


class ProfileService:

    def __init__(self, user_repo: UserRepository,
                 game_repo: ChessGameRepository,
                 rating_repo: RatingHistoryRepository):
        self.user_repo = user_repo
        self.game_repo = game_repo
        self.rating_repo = rating_repo

    async def fetch_profile_data(self, user_id: int) -> ProfileResponse:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        return ProfileResponse(
            id=user.id,
            username=user.username,
            current_rating=user.current_rating,
            games_played=user.games_played,
            wins=user.wins,
            losses=user.losses,
            draws=user.draws,
        )

    async def fetch_game_history(self, user_id: int) -> list[GameHistoryItem]:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        games = await self.game_repo.get_user_games(user_id)

        history = []
        for game in games:
            played_white = (game.white_player_id == user_id)
            opponent_id = game.black_player_id if played_white else game.white_player_id
            opponent = await self.user_repo.get_by_id(opponent_id)
            
            history.append(GameHistoryItem(
                game_id=game.id,
                opponent_username=opponent.username,
                played_as="white" if played_white else "black",
                result=game.result,
                outcome=self._outcome_for_user(game, user_id),
                status=game.status,
                started_at=game.started_at.isoformat() if game.started_at else None,
            ))

        return history

    async def generate_rating_chart_points(self, user_id: int) -> list[RatingPoint]:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        snapshots = await self.rating_repo.get_user_history(user_id)

        return [
            RatingPoint(
                date=snap.date.isoformat() if snap.date else None,
                rating=snap.rating,
            )
            for snap in snapshots
        ]

    def _outcome_for_user(self, game, user_id: int) -> str:
        if game.status != "finished":
            return "ongoing"
        if game.winner_id is None:
            return "draw"
        return "win" if game.winner_id == user_id else "loss"