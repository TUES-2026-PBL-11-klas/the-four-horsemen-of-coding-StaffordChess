from __future__ import annotations

from app.domain.piece import Piece


class Square:

    def __init__(self, x: int, y: int, piece: Piece = None):
        self.x = x
        self.y = y
        self.piece = piece

    def get_piece_color(self):
        if self.piece:
            return self.piece.color
        return None

    def set_piece(self, piece: Piece) -> None:
        self.piece = piece

    def remove_piece(self) -> Piece:
        removed = self.piece
        self.piece = None
        return removed

    def has_piece(self) -> bool:
        return self.piece is not None

    def algebraic_notation(self) -> str:
        file = chr(ord('a') + self.y)
        rank = str(8 - self.x)
        return file + rank

    def is_light_square(self) -> bool:
        return (self.x + self.y) % 2 == 0

    def __eq__(self, other) -> bool:
        if not isinstance(other, Square):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))