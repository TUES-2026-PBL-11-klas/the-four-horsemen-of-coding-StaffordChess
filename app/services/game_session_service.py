from __future__ import annotations

from fastapi import HTTPException

from app.domain.chess_engine import ChessEngine
from app.domain.game_clock import GameClock
from app.domain.color import Color
from app.domain.move import Move
from app.repositories.chess_game_repository import ChessGameRepository
from app.domain.game_result import GameResult

def _square_to_coordinates(square: str) -> tuple[int, int]:
    if len(square) != 2:
        raise ValueError(f"Invalid square notation: {square}")
    file_char = square[0].lower()
    rank_char = square[1]
    if file_char < "a" or file_char > "h" or rank_char < "1" or rank_char > "8":
        raise ValueError(f"Invalid square notation: {square}")
    col = ord(file_char) - ord("a")
    row = 8 - int(rank_char)
    return row, col


class GameSessionService:

    def __init__(self, game_id: int, white_user_id: int, black_user_id: int,
                 game_repo: ChessGameRepository,
                 initial_seconds: int = 300, increment_seconds: int = 0):
        self.game_id = game_id
        self.white_user_id = white_user_id
        self.black_user_id = black_user_id
        self.game_repo = game_repo

        self.engine = ChessEngine()
        self.clock = GameClock(initial_seconds, increment_seconds)
        self.is_started = False


    def _user_color(self, user_id: int) -> Color:
        if user_id == self.white_user_id:
            return Color.WHITE
        if user_id == self.black_user_id:
            return Color.BLACK
        raise HTTPException(status_code=403, detail="You are not a player in this game")

    def _find_legal_move(self, from_sq: str, to_sq: str) -> Move:
        from_row, from_col = _square_to_coordinates(from_sq)
        to_row, to_col = _square_to_coordinates(to_sq)

        for move in self.engine.get_all_legal_moves():
            if (move.start_square.x == from_row and move.start_square.y == from_col
                    and move.end_square.x == to_row and move.end_square.y == to_col):
                return move

        raise HTTPException(status_code=400, detail=f"Illegal move: {from_sq}->{to_sq}")


    async def handle_incoming_move(self, user_id: int, from_sq: str, to_sq: str) -> dict:
        if self.engine.game_result.is_game_over():
            raise HTTPException(status_code=400, detail="Game is already over")

        player_color = self._user_color(user_id)
        if player_color != self.engine.current_turn:
            raise HTTPException(status_code=400, detail="Not your turn")

        move = self._find_legal_move(from_sq, to_sq)
        self.engine.make_move(move)
        self.clock.switch_turn()


        if self.engine.is_checkmate():
            winner_id = self.white_user_id if player_color == Color.WHITE else self.black_user_id
            if player_color == Color.WHITE:
                self.engine.game_result.set_result(GameResult.Result.WHITE_WINS, "checkmate")
                result = "white_wins"
            else:
                self.engine.game_result.set_result(GameResult.Result.BLACK_WINS, "checkmate")
                result = "black_wins"
            await self.end_game(winner_id, result)
        elif self.engine.is_stalemate():
            self.engine.game_result.set_result(GameResult.Result.DRAW, "stalemate")
            await self.end_game(None, "draw")

        return self.get_state()

    def get_state(self) -> dict:
        return {
            "game_id": self.game_id,
            "fen": self.engine.to_fen(),
            "turn": "white" if self.engine.current_turn == Color.WHITE else "black",
            "white_time": self.clock.get_time(Color.WHITE),
            "black_time": self.clock.get_time(Color.BLACK),
            "is_check": self.engine.is_in_check(self.engine.current_turn),
            "is_game_over": self.engine.game_result.is_game_over(),
            "result": self.engine.game_result.result.value,
        }

    async def end_game(self, winner_id: int | None, result_type: str) -> None:
        self.clock.stop()
        game = await self.game_repo.get_by_id(self.game_id)
        if game is not None:
            moves_pgn = self._build_pgn()
            await self.game_repo.finish(game, moves_pgn, result_type, winner_id)

    async def resign(self, user_id: int) -> dict:
        player_color = self._user_color(user_id)
        winner_id = self.black_user_id if player_color == Color.WHITE else self.white_user_id
        
        self.engine.set_current_turn(player_color)
        self.engine.resign()
        
        result_str = "black_wins" if winner_id == self.black_user_id else "white_wins"
        await self.end_game(winner_id, f"{result_str}_by_resignation")
        
        return self.get_state()

    def _build_pgn(self) -> str:
        parts = []
        for move in self.engine.move_history:
            parts.append(move.start_square.algebraic_notation()
                         + move.end_square.algebraic_notation())
        return " ".join(parts)