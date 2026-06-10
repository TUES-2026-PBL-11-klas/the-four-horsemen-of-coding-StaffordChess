from __future__ import annotations

from fastapi import HTTPException

from app.domain.chess_engine import ChessEngine
from app.domain.game_clock import GameClock
from app.domain.color import Color
from app.domain.move import Move
from app.domain.piece import Bishop, Knight, Queen, Rook
from app.repositories.chess_game_repository import ChessGameRepository
from app.repositories.user_repository import UserRepository
from app.repositories.rating_history_repository import RatingHistoryRepository
from app.services.rating_service import RatingService
from app.domain.game_result import GameResult


_PROMOTION_PIECES = {
    "q": Queen,
    "r": Rook,
    "b": Bishop,
    "n": Knight,
}


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
                 initial_seconds: int = 300, increment_seconds: int = 0,
                 user_repo: UserRepository | None = None,
                 rating_repo: RatingHistoryRepository | None = None):
        self.game_id = game_id
        self.white_user_id = white_user_id
        self.black_user_id = black_user_id
        self.game_repo = game_repo
        self.user_repo = user_repo
        self.rating_repo = rating_repo

        self.engine = ChessEngine()
        self.clock = GameClock(initial_seconds, increment_seconds)
        self.is_started = False
        self._finalized = False

    async def hydrate_from_history(self, pgn_history: str | None):
        if not pgn_history:
            return

        for token in pgn_history.strip().split():
            if len(token) < 4:
                raise ValueError(f"Invalid UCI token in history: {token!r}")

            from_sq, to_sq = token[:2], token[2:4]
            promotion_letter = token[4].lower() if len(token) >= 5 else None

            move = self._find_legal_move(from_sq, to_sq, promotion_letter)
            self.engine.make_move(move)

    def _user_color(self, user_id: int) -> Color:
        if user_id == self.white_user_id:
            return Color.WHITE
        if user_id == self.black_user_id:
            return Color.BLACK
        raise HTTPException(status_code=403, detail="You are not a player in this game")

    def _find_legal_move(self, from_sq: str, to_sq: str,
                         promotion: str | None = None) -> Move:
        from_row, from_col = _square_to_coordinates(from_sq)
        to_row, to_col = _square_to_coordinates(to_sq)

        fallback_promotion_move: Move | None = None

        for move in self.engine.get_all_legal_moves():
            if not (move.start_square.x == from_row and move.start_square.y == from_col
                    and move.end_square.x == to_row and move.end_square.y == to_col):
                continue

            if move.is_pawn_promotion:
                if promotion is None:
                    if isinstance(move.promotion_piece, Queen):
                        fallback_promotion_move = move
                    continue
                expected_cls = _PROMOTION_PIECES.get(promotion)
                if expected_cls is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid promotion piece: {promotion}",
                    )
                if isinstance(move.promotion_piece, expected_cls):
                    return move
                continue

            return move

        if fallback_promotion_move is not None:
            return fallback_promotion_move

        detail = f"Illegal move: {from_sq}->{to_sq}"
        if promotion:
            detail += promotion
        raise HTTPException(status_code=400, detail=detail)


    async def handle_incoming_move(self, user_id: int, from_sq: str, to_sq: str,
                                   promotion: str | None = None) -> dict:
        if self.engine.game_result.is_game_over():
            raise HTTPException(status_code=400, detail="Game is already over")

        player_color = self._user_color(user_id)
        if player_color != self.engine.current_turn:
            raise HTTPException(status_code=400, detail="Not your turn")

        if self.is_started and self.clock.is_time_up(player_color):
            await self._end_on_time(player_color)
            return self.get_state()

        move = self._find_legal_move(from_sq, to_sq, promotion)
        self.engine.make_move(move)
        self.clock.switch_turn()

        if self.engine.is_checkmate():
            if player_color == Color.WHITE:
                self.engine.game_result.set_result(GameResult.Result.WHITE_WINS, "checkmate")
                winner_id, result = self.white_user_id, "white_wins"
            else:
                self.engine.game_result.set_result(GameResult.Result.BLACK_WINS, "checkmate")
                winner_id, result = self.black_user_id, "black_wins"
            await self.end_game(winner_id, result)
        elif self.engine.is_stalemate():
            self.engine.game_result.set_result(GameResult.Result.DRAW, "stalemate")
            await self.end_game(None, "draw")

        return self.get_state()

    async def check_time(self) -> dict:
        if self.is_started and not self.engine.game_result.is_game_over():
            active = self.engine.current_turn
            if self.clock.is_time_up(active):
                await self._end_on_time(active)
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
            "winner_id": self._compute_winner_id(),
        }
    
    def _compute_winner_id(self) -> int | None:
        r = self.engine.game_result.result
        if r in (GameResult.Result.WHITE_WINS, GameResult.Result.BLACK_RESIGNS):
            return self.white_user_id
        if r in (GameResult.Result.BLACK_WINS, GameResult.Result.WHITE_RESIGNS):
            return self.black_user_id
        return None
    
    
    async def _end_on_time(self, loser_color: Color) -> None:
        if loser_color == Color.WHITE:
            self.engine.game_result.set_result(GameResult.Result.BLACK_WINS, "white ran out of time")
            winner_id, result_type = self.black_user_id, "black_wins_on_time"
        else:
            self.engine.game_result.set_result(GameResult.Result.WHITE_WINS, "black ran out of time")
            winner_id, result_type = self.white_user_id, "white_wins_on_time"
        await self.end_game(winner_id, result_type)

    async def end_game(self, winner_id: int | None, result_type: str) -> None:
        if self._finalized:
            return
        self._finalized = True

        self.clock.stop()
        game = await self.game_repo.get_by_id(self.game_id)
        if game is not None:
            move_text = self._build_pgn()
            await self.game_repo.finish(game, move_text, result_type, winner_id)

        if self.user_repo is not None and self.rating_repo is not None:
            rating_service = RatingService(self.user_repo, self.rating_repo)
            await rating_service.apply(self.white_user_id, self.black_user_id, winner_id)

    async def resign(self, user_id: int) -> dict:
        if self.engine.game_result.is_game_over():
            raise HTTPException(status_code=400, detail="Game is already over")

        player_color = self._user_color(user_id)
        if player_color == Color.WHITE:
            self.engine.game_result.set_result(GameResult.Result.WHITE_RESIGNS, "white resigned")
            winner_id, result_type = self.black_user_id, "black_wins_by_resignation"
        else:
            self.engine.game_result.set_result(GameResult.Result.BLACK_RESIGNS, "black resigned")
            winner_id, result_type = self.white_user_id, "white_wins_by_resignation"

        await self.end_game(winner_id, result_type)
        return self.get_state()

    def _build_pgn(self) -> str:
        parts = []
        for move in self.engine.move_history:
            uci = move.start_square.algebraic_notation() + move.end_square.algebraic_notation()
            if move.is_pawn_promotion and move.promotion_piece is not None:
                uci += move.promotion_piece.get_piece_symbol().lower()
            parts.append(uci)
        return " ".join(parts)