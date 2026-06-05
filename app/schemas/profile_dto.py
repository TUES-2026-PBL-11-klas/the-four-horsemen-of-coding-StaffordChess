from pydantic import BaseModel


class ProfileResponse(BaseModel):
    id: int
    username: str
    current_rating: int
    games_played: int
    wins: int
    losses: int
    draws: int


class GameHistoryItem(BaseModel):
    game_id: int
    opponent_username: str
    played_as: str
    result: str | None
    outcome: str
    status: str
    started_at: str | None


class RatingPoint(BaseModel):
    date: str | None
    rating: int