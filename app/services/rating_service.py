from __future__ import annotations

from app.repositories.user_repository import UserRepository
from app.repositories.rating_history_repository import RatingHistoryRepository


class RatingService:
    def __init__(self, user_repo: UserRepository, rating_repo: RatingHistoryRepository,
                 k_factor: int = 32):
        self.user_repo = user_repo
        self.rating_repo = rating_repo
        self.k_factor = k_factor

    @staticmethod
    def _expected_score(rating: int, opponent_rating: int) -> float:
        return 1.0 / (1.0 + 10 ** ((opponent_rating - rating) / 400.0))

    def _new_rating(self, rating: int, opponent_rating: int, actual: float) -> int:
        expected = self._expected_score(rating, opponent_rating)
        return round(rating + self.k_factor * (actual - expected))

    async def apply(self, white_id: int, black_id: int, winner_id: int | None) -> None:
        white = await self.user_repo.get_by_id(white_id)
        black = await self.user_repo.get_by_id(black_id)
        if white is None or black is None:
            return

        if winner_id is None:
            white_actual, black_actual = 0.5, 0.5
        elif winner_id == white_id:
            white_actual, black_actual = 1.0, 0.0
        else:
            white_actual, black_actual = 0.0, 1.0

        white_old = white.current_rating
        black_old = black.current_rating

        white.current_rating = self._new_rating(white_old, black_old, white_actual)
        black.current_rating = self._new_rating(black_old, white_old, black_actual)

        white.games_played += 1
        black.games_played += 1
        if winner_id is None:
            white.draws += 1
            black.draws += 1
        elif winner_id == white_id:
            white.wins += 1
            black.losses += 1
        else:
            black.wins += 1
            white.losses += 1

        await self.rating_repo.add_snapshot(white_id, white.current_rating)
        await self.rating_repo.add_snapshot(black_id, black.current_rating)

        await self.user_repo.db.commit()