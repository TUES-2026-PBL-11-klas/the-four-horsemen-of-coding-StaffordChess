from __future__ import annotations

from app.domain.piece import Piece
from app.domain.square import Square


class Move:

    def __init__(self, start_square: Square, end_square: Square):
        if start_square.piece is None:
            raise ValueError("Start square must have a piece to move.")
        if start_square.algebraic_notation() == end_square.algebraic_notation():
            raise ValueError("Start and end squares must be different.")
        self.start_square = start_square
        self.end_square = end_square
        self.piece_moved = start_square.piece
        self.piece_captured = end_square.piece
        self.has_piece_moved = self.piece_moved.has_moved
        self.is_en_passant = False
        self.en_passant_captured_square = None
        self.is_pawn_promotion = False
        self.promotion_piece = None
        self.is_king_castling = False
        self.is_queen_castling = False

    @classmethod
    def copy_of(cls, other: Move) -> Move:
        new = cls.__new__(cls)
        new.start_square = other.start_square
        new.end_square = other.end_square
        new.piece_moved = other.piece_moved
        new.piece_captured = other.piece_captured
        new.has_piece_moved = other.has_piece_moved
        new.is_en_passant = other.is_en_passant
        new.en_passant_captured_square = other.en_passant_captured_square
        new.is_pawn_promotion = other.is_pawn_promotion
        new.promotion_piece = other.promotion_piece
        new.is_king_castling = other.is_king_castling
        new.is_queen_castling = other.is_queen_castling
        return new

    def are_two_moves_equal(self, other_move) -> bool:
        if not isinstance(other_move, Move):
            return False
        if self.start_square.algebraic_notation() != other_move.start_square.algebraic_notation():
            return False
        if self.end_square.algebraic_notation() != other_move.end_square.algebraic_notation():
            return False
        if self.piece_moved.get_piece_type() != other_move.piece_moved.get_piece_type():
            return False
        return True

    def get_move_in_notation(self) -> str:
        if self.is_king_castling:
            return "O-O"
        if self.is_queen_castling:
            return "O-O-O"

        piece_symbol = self.piece_moved.get_piece_symbol()
        if piece_symbol == "P":
            piece_symbol = ""
            if self.piece_captured:
                piece_symbol = self.start_square.algebraic_notation()[0]

        move = piece_symbol
        move += "x" if self.piece_captured else ""
        move += self.end_square.algebraic_notation()
        if self.is_pawn_promotion and self.promotion_piece:
            move += "=" + self.promotion_piece.get_piece_symbol()
        return move