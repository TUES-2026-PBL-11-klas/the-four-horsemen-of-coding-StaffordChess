from __future__ import annotations
from enum import Enum


class Color(Enum):
    WHITE = "white"
    BLACK = "black"

    def get_opposite_color(self) -> Color:
        if self == Color.WHITE:
            return Color.BLACK
        return Color.WHITE

    def get_pawn_direction(self) -> int:
        if self == Color.WHITE:
            return -1
        return 1