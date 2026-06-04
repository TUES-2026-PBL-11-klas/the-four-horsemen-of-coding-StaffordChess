from __future__ import annotations

from app.domain.board import Board
from app.domain.color import Color
from app.domain.game_result import GameResult
from app.domain.move import Move
from app.domain.piece import Bishop, Knight, Queen, Rook
from app.domain.square import Square


class ChessEngine:
    board: Board
    move_history: list[Move]
    current_turn: Color
    game_result: GameResult
    draw_requested_by: Color | None

    def __init__(self):
        self.board = Board()
        self.move_history: list[Move] = []
        self.current_turn = Color.WHITE
        self.game_result = GameResult()
        self.draw_requested_by: Color | None = None

    def clear_draw_request(self) -> None:
        self.draw_requested_by = None

    def set_current_turn(self, color: Color) -> None:
        self.current_turn = color


    def make_move(self, move: Move, switch_turn: bool = True) -> None:
       
        start = move.start_square
        end = move.end_square
        piece = move.piece_moved

        move.has_piece_moved = piece.has_moved

        end.set_piece(piece)
        start.remove_piece()
        piece.has_moved = True

        if move.is_en_passant:
            move.en_passant_captured_square.remove_piece()

        if move.is_pawn_promotion:
            end.set_piece(move.promotion_piece)

        if move.is_king_castling:
            row = start.x
            rook_start = self.board.get_square(row, 7)
            rook_end = self.board.get_square(row, 5)
            rook = rook_start.piece
            rook_end.set_piece(rook)
            rook_start.remove_piece()
            rook.has_moved = True
        if move.is_queen_castling:
            row = start.x
            rook_start = self.board.get_square(row, 0)
            rook_end = self.board.get_square(row, 3)
            rook = rook_start.piece
            rook_end.set_piece(rook)
            rook_start.remove_piece()
            rook.has_moved = True

        self.move_history.append(move)
        if switch_turn:
            self.current_turn = self.current_turn.get_opposite_color()

    def undo_move(self, switch_turn: bool = True) -> None:
        if not self.move_history:
            return

        move = self.move_history.pop()
        start = move.start_square
        end = move.end_square
        piece = move.piece_moved
        captured = move.piece_captured

        if move.is_en_passant:
            start.set_piece(piece)
            end.remove_piece()
            move.en_passant_captured_square.set_piece(captured)
            piece.has_moved = move.has_piece_moved
            if switch_turn:
                self.current_turn = self.current_turn.get_opposite_color()
            return

        if move.is_king_castling or move.is_queen_castling:
            row = start.x
            start.set_piece(piece)
            end.remove_piece()
            piece.has_moved = move.has_piece_moved

            if move.is_king_castling:
                rook_end = self.board.get_square(row, 5)
                rook_start = self.board.get_square(row, 7)
            else:
                rook_end = self.board.get_square(row, 3)
                rook_start = self.board.get_square(row, 0)
            rook = rook_end.piece
            rook_start.set_piece(rook)
            rook_end.remove_piece()
            rook.has_moved = False

            if switch_turn:
                self.current_turn = self.current_turn.get_opposite_color()
            return

        start.set_piece(piece)
        end.set_piece(captured)
        piece.has_moved = move.has_piece_moved
        if switch_turn:
            self.current_turn = self.current_turn.get_opposite_color()


    def find_king(self, color: Color) -> Square:
        for row in range(8):
            for col in range(8):
                square = self.board.get_square(row, col)
                piece = square.piece
                if piece is not None and piece.get_piece_type() == "King" and piece.color == color:
                    return square
        raise ValueError(f"King not found for color: {color}")

    def is_square_under_attack(self, row: int, col: int, by_color: Color) -> bool:
        attacker_moves = self.get_all_possible_moves(by_color)
        for move in attacker_moves:
            if move.end_square.x == row and move.end_square.y == col:
                return True
        return False

    def is_in_check(self, color: Color) -> bool:
        king_square = self.find_king(color)
        opponent = color.get_opposite_color()
        return self.is_square_under_attack(king_square.x, king_square.y, opponent)


    def get_all_legal_moves(self) -> list[Move]:
        possible_moves = self.get_all_possible_moves(self.current_turn)
        legal_moves: list[Move] = []

        for move in possible_moves:
            if move.is_king_castling or move.is_queen_castling:
                if not self._castle_is_legal(move):
                    continue

            self.make_move(move, switch_turn=False)
            in_check = self.is_in_check(move.piece_moved.color)
            self.undo_move(switch_turn=False)

            if not in_check:
                legal_moves.append(move)

        return legal_moves

    def _castle_is_legal(self, move: Move) -> bool:
        king_color = move.piece_moved.color
        opponent = king_color.get_opposite_color()
        row = move.start_square.x
        start_col = move.start_square.y

        if self.is_in_check(king_color):
            return False

        if move.is_king_castling:
            intermediate_col = start_col + 1
        else:
            intermediate_col = start_col - 1
        if self.is_square_under_attack(row, intermediate_col, opponent):
            return False

        return True


    def is_checkmate(self) -> bool:
        return len(self.get_all_legal_moves()) == 0 and self.is_in_check(self.current_turn)

    def is_stalemate(self) -> bool:
        return len(self.get_all_legal_moves()) == 0 and not self.is_in_check(self.current_turn)


    def get_all_possible_moves(self, color: Color) -> list[Move]:
        possible_moves: list[Move] = []
        for row in range(8):
            for col in range(8):
                square = self.board.get_square(row, col)
                piece = square.piece
                if piece is None or piece.color != color:
                    continue

                piece_type = piece.get_piece_type()
                if piece_type == "Pawn":
                    self.get_pawn_moves(square, possible_moves)
                elif piece_type == "Knight":
                    self.get_knight_moves(square, possible_moves)
                elif piece_type == "King":
                    self.get_king_moves(square, possible_moves)
                else:
                    self.get_slider_moves(square, possible_moves)

        return possible_moves

    def get_slider_moves(self, start: Square, possible_moves: list[Move]) -> None:
        piece = start.piece
        raw = piece.get_possible_moves((start.x, start.y))

        direction_blocked = False
        last_direction = (1000, 1000)

        for new_row, new_col, d_row, d_col in raw:
            if (d_row, d_col) != last_direction:
                direction_blocked = False
                last_direction = (d_row, d_col)

            if direction_blocked:
                continue

            target = self.board.get_square(new_row, new_col)
            target_piece = target.piece
            if target_piece is None:
                possible_moves.append(Move(start, target))
            else:
                if target_piece.color != piece.color:
                    possible_moves.append(Move(start, target))
                direction_blocked = True

    def get_knight_moves(self, start: Square, possible_moves: list[Move]) -> None:
        piece = start.piece
        for new_row, new_col in piece.get_possible_moves((start.x, start.y)):
            target = self.board.get_square(new_row, new_col)
            target_piece = target.piece
            if target_piece is None or target_piece.color != piece.color:
                possible_moves.append(Move(start, target))

    def get_king_moves(self, start: Square, possible_moves: list[Move]) -> None:
        king = start.piece
        for new_row, new_col in king.get_possible_moves((start.x, start.y)):
            target = self.board.get_square(new_row, new_col)
            target_piece = target.piece
            if target_piece is None or target_piece.color != king.color:
                possible_moves.append(Move(start, target))

        self.add_castling_moves(start, possible_moves)

    def add_castling_moves(self, start: Square, possible_moves: list[Move]) -> None:
        king = start.piece
        if king.has_moved:
            return

        king_row = start.x
        king_col = start.y

        ks_rook_sq = self.board.get_square(king_row, 7)
        ks_rook = ks_rook_sq.piece
        if (ks_rook is not None and ks_rook.get_piece_type() == "Rook"
                and ks_rook.color == king.color and not ks_rook.has_moved):
            path_clear = all(
                self.board.get_square(king_row, c).piece is None
                for c in range(king_col + 1, 7)
            )
            if path_clear:
                target = self.board.get_square(king_row, king_col + 2)
                castle = Move(start, target)
                castle.is_king_castling = True
                possible_moves.append(castle)

        qs_rook_sq = self.board.get_square(king_row, 0)
        qs_rook = qs_rook_sq.piece
        if (qs_rook is not None and qs_rook.get_piece_type() == "Rook"
                and qs_rook.color == king.color and not qs_rook.has_moved):
            path_clear = all(
                self.board.get_square(king_row, c).piece is None
                for c in range(1, king_col)
            )
            if path_clear:
                target = self.board.get_square(king_row, king_col - 2)
                castle = Move(start, target)
                castle.is_queen_castling = True
                possible_moves.append(castle)

    def get_pawn_moves(self, start: Square, possible_moves: list[Move]) -> None:
        pawn = start.piece
        raw = pawn.get_possible_moves((start.x, start.y))

        for new_row, new_col in raw:
            target = self.board.get_square(new_row, new_col)
            target_piece = target.piece
            same_column = (new_col == start.y)
            diagonal = abs(new_col - start.y) == 1
            move_added = False

            if same_column:
                if target_piece is not None:
                    continue
                if abs(new_row - start.x) == 2:
                    mid_row = (new_row + start.x) // 2
                    if self.board.get_square(mid_row, new_col).piece is not None:
                        continue
                possible_moves.append(Move(start, target))
                move_added = True

            if diagonal:
                if target_piece is None:
                    self.add_en_passant(start, new_row, new_col, possible_moves)
                    continue
                if target_piece.color != pawn.color:
                    possible_moves.append(Move(start, target))
                    move_added = True

            if move_added:
                last = possible_moves[-1]
                end_row = last.end_square.x
                if end_row == 0 or end_row == 7:
                    self.expand_promotion(last, possible_moves)

    def add_en_passant(self, start: Square, target_row: int,
                              target_col: int, possible_moves: list[Move]) -> None:
        if not self.move_history:
            return

        last = self.move_history[-1]
        if last.piece_moved.get_piece_type() != "Pawn":
            return

        pawn = start.piece
        pawn_row = start.x
        pawn_col = start.y
        last_start_row = last.start_square.x
        last_end_row = last.end_square.x
        last_end_col = last.end_square.y

        if abs(last_start_row - last_end_row) != 2:
            return
        if last_end_row != pawn_row:
            return
        if abs(last_end_col - pawn_col) != 1:
            return

        direction = pawn.color.get_pawn_direction()
        ep_row = pawn_row + direction
        ep_col = last_end_col
        if ep_row != target_row or ep_col != target_col:
            return
        ep_square = self.board.get_square(ep_row, ep_col)
        if ep_square.piece is not None:
            return

        ep_move = Move(start, ep_square)
        ep_move.is_en_passant = True
        ep_move.piece_captured = last.piece_moved
        ep_move.en_passant_captured_square = last.end_square
        possible_moves.append(ep_move)

    def expand_promotion(self, move: Move, possible_moves: list[Move]) -> None:
        color = move.piece_moved.color
        move.is_pawn_promotion = True
        move.promotion_piece = Queen(color)

        for piece_cls in (Rook, Bishop, Knight):
            alt = Move.copy_of(move)
            alt.promotion_piece = piece_cls(color)
            possible_moves.append(alt)


    def resign(self) -> None:
        if self.current_turn == Color.WHITE:
            result = GameResult.Result.WHITE_RESIGNS
        else:
            result = GameResult.Result.BLACK_RESIGNS
        self.game_result.set_result(result, f"{self.current_turn} resigned")

    def request_draw(self) -> bool:
        if self.draw_requested_by is None:
            self.draw_requested_by = self.current_turn
            return False
        if self.draw_requested_by == self.current_turn:
            return False
        self.game_result.set_result(GameResult.Result.DRAW, "Draw agreed by both players")
        self.draw_requested_by = None
        return True

    def accept_draw(self) -> None:
        if self.draw_requested_by is None:
            raise ValueError("No draw request to accept")
        if self.draw_requested_by == self.current_turn:
            raise ValueError("You cannot accept your own draw request")
        self.game_result.set_result(GameResult.Result.DRAW, "Draw agreed by both players")
        self.draw_requested_by = None

    def decline_draw(self) -> None:
        if self.draw_requested_by is None:
            raise ValueError("No draw request to decline")
        self.draw_requested_by = None