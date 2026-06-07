from __future__ import annotations
from enum import Enum


class GameResult:

    class Result(Enum):
        ONGOING = "Ongoing"
        WHITE_WINS = "White wins"
        BLACK_WINS = "Black wins"
        DRAW = "Draw"
        WHITE_RESIGNS = "White resigns"
        BLACK_RESIGNS = "Black resigns"

    def __init__(self, result: Result = Result.ONGOING, reason: str = "game is ongoing"):
        self.result = result
        self.reason = reason

    def set_result(self, result: Result, reason: str) -> None:
        self.result = result
        self.reason = reason

    def is_game_over(self) -> bool:
        return self.result != GameResult.Result.ONGOING