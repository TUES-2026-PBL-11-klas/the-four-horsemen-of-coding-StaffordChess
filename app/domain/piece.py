from __future__ import annotations
from abc import ABC, abstractmethod

from app.domain.color import Color


class Piece(ABC):

    def __init__(self, color: Color):
        self.color = color
        self.has_moved = False

    @abstractmethod
    def get_possible_moves(self, position: tuple[int, int]) -> list[tuple[int, int]]:
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_piece_type(self) -> str:
        return self.__class__.__name__

    def get_piece_symbol(self) -> str:
        piece = self.get_piece_type()
        if piece == "Knight":
            return "N"
        if piece == "Pawn":
            return "P"
        return piece[0]


class Pawn(Piece):

    def get_possible_moves(self, position: tuple[int, int]) -> list[tuple[int, int]]:
        moves = []
        direction = self.color.get_pawn_direction()

        new_row = position[0] + direction
        if 0 <= new_row < 8:
            moves.append((new_row, position[1]))
            if not self.has_moved:
                new_row2 = position[0] + 2 * direction
                if 0 <= new_row2 < 8:
                    moves.append((new_row2, position[1]))

        for col_offset in (-1, 1):
            new_col = position[1] + col_offset
            new_row = position[0] + direction
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                moves.append((new_row, new_col))

        return moves


class Rook(Piece):

    def get_possible_moves(self, position: tuple[int, int]) -> list[tuple[int, int]]:
        moves = []
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for dr, dc in directions:
            for i in range(1, 8):
                new_row = position[0] + dr * i
                new_col = position[1] + dc * i
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    moves.append((new_row, new_col))
                else:
                    break
        return moves


class Knight(Piece):

    def get_possible_moves(self, position: tuple[int, int]) -> list[tuple[int, int]]:
        moves = []
        offsets = [(2, 1), (2, -1), (-2, 1), (-2, -1),
                   (1, 2), (1, -2), (-1, 2), (-1, -2)]
        for dr, dc in offsets:
            new_row = position[0] + dr
            new_col = position[1] + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                moves.append((new_row, new_col))
        return moves


class Bishop(Piece):

    def get_possible_moves(self, position: tuple[int, int]) -> list[tuple[int, int]]:
        moves = []
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in directions:
            for i in range(1, 8):
                new_row = position[0] + dr * i
                new_col = position[1] + dc * i
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    moves.append((new_row, new_col))
                else:
                    break
        return moves


class Queen(Piece):

    def get_possible_moves(self, position: tuple[int, int]) -> list[tuple[int, int]]:
        moves = []
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1),
                      (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in directions:
            for i in range(1, 8):
                new_row = position[0] + dr * i
                new_col = position[1] + dc * i
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    moves.append((new_row, new_col))
                else:
                    break
        return moves


class King(Piece):

    def get_possible_moves(self, position: tuple[int, int]) -> list[tuple[int, int]]:
        moves = []
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1),
                      (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in directions:
            new_row = position[0] + dr
            new_col = position[1] + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                moves.append((new_row, new_col))
        return moves