from __future__ import annotations

from app.domain.color import Color
from app.domain.piece import Bishop, King, Knight, Pawn, Queen, Rook
from app.domain.square import Square


class Board:
    squares: list[list[Square]]

    def __init__(self):
        self.squares: list[list[Square]] = [[None] * 8 for _ in range(8)]
        self.init_empty_board()
        self.set_starting_position()

    def init_empty_board(self) -> None:
        for row in range(8):
            for col in range(8):
                self.squares[row][col] = Square(row, col)

    def set_starting_position(self) -> None:
        for col in range(8):
            self.squares[6][col].set_piece(Pawn(Color.WHITE))
            self.squares[1][col].set_piece(Pawn(Color.BLACK))

            if col == 0 or col == 7:
                self.squares[7][col].set_piece(Rook(Color.WHITE))
                self.squares[0][col].set_piece(Rook(Color.BLACK))
            if col == 1 or col == 6:
                self.squares[7][col].set_piece(Knight(Color.WHITE))
                self.squares[0][col].set_piece(Knight(Color.BLACK))
            if col == 2 or col == 5:
                self.squares[7][col].set_piece(Bishop(Color.WHITE))
                self.squares[0][col].set_piece(Bishop(Color.BLACK))
            if col == 3:
                self.squares[7][col].set_piece(Queen(Color.WHITE))
                self.squares[0][col].set_piece(Queen(Color.BLACK))
            if col == 4:
                self.squares[7][col].set_piece(King(Color.WHITE))
                self.squares[0][col].set_piece(King(Color.BLACK))

    def get_square(self, x: int, y: int) -> Square:
        if x < 0 or x > 7 or y < 0 or y > 7:
            raise ValueError("Square coordinates must be between 0 and 7.")
        return self.squares[x][y]

    def get_square_by_algebraic_notation(self, notation: str) -> Square:
        if len(notation) != 2:
            raise ValueError("Algebraic notation must be 2 characters long.")
        file = notation[0]
        rank = notation[1]
        if file < 'a' or file > 'h' or rank < '1' or rank > '8':
            raise ValueError("Algebraic notation must be between a1 and h8.")
        y = ord(file) - ord('a')
        x = 8 - int(rank)
        return self.get_square(x, y)

    def get_all_squares(self) -> list[list[Square]]:
        return self.squares