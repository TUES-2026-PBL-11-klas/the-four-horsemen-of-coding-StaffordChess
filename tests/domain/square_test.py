import pytest

from app.domain.color import Color
from app.domain.square import Square
from app.domain.piece import Pawn, Queen



def test_square_stores_coordinates():
    sq = Square(3, 4)
    assert sq.x == 3
    assert sq.y == 4


def test_square_empty_by_default():
    sq = Square(0, 0)
    assert sq.piece is None


def test_square_can_hold_piece_at_construction():
    pawn = Pawn(Color.WHITE)
    sq = Square(6, 4, pawn)
    assert sq.piece is pawn



def test_set_piece():
    sq = Square(0, 0)
    pawn = Pawn(Color.WHITE)
    sq.set_piece(pawn)
    assert sq.piece is pawn


def test_has_piece_true_when_occupied():
    sq = Square(0, 0, Pawn(Color.WHITE))
    assert sq.has_piece() is True


def test_has_piece_false_when_empty():
    sq = Square(0, 0)
    assert sq.has_piece() is False


def test_remove_piece_returns_it():
    pawn = Pawn(Color.WHITE)
    sq = Square(0, 0, pawn)
    removed = sq.remove_piece()
    assert removed is pawn


def test_remove_piece_clears_square():
    sq = Square(0, 0, Pawn(Color.WHITE))
    sq.remove_piece()
    assert sq.piece is None


def test_remove_piece_from_empty_returns_none():
    sq = Square(0, 0)
    assert sq.remove_piece() is None



def test_get_piece_color_when_occupied():
    sq = Square(0, 0, Pawn(Color.BLACK))
    assert sq.get_piece_color() == Color.BLACK


def test_get_piece_color_when_empty_returns_none():
    sq = Square(0, 0)
    assert sq.get_piece_color() is None



def test_algebraic_notation_corners():
    assert Square(7, 0).algebraic_notation() == "a1"
    assert Square(0, 0).algebraic_notation() == "a8"
    assert Square(0, 7).algebraic_notation() == "h8"
    assert Square(7, 7).algebraic_notation() == "h1"


def test_algebraic_notation_center():
    assert Square(4, 4).algebraic_notation() == "e4"
    assert Square(3, 3).algebraic_notation() == "d5"


@pytest.mark.parametrize("x,y,expected", [
    (7, 0, "a1"), (7, 1, "b1"), (7, 2, "c1"), (7, 3, "d1"),
    (7, 4, "e1"), (7, 5, "f1"), (7, 6, "g1"), (7, 7, "h1"),
    (0, 0, "a8"), (0, 4, "e8"),
])
def test_algebraic_notation_parametrized(x, y, expected):
    assert Square(x, y).algebraic_notation() == expected



def test_a1_is_dark():
    assert Square(7, 0).is_light_square() is False


def test_h1_is_light():
    assert Square(7, 7).is_light_square() is True


def test_a8_is_light():
    assert Square(0, 0).is_light_square() is True


def test_adjacent_squares_alternate_color():
    a1 = Square(7, 0)
    b1 = Square(7, 1)
    assert a1.is_light_square() != b1.is_light_square()



def test_squares_with_same_coords_are_equal():
    assert Square(3, 4) == Square(3, 4)


def test_squares_with_different_coords_not_equal():
    assert Square(3, 4) != Square(4, 3)


def test_square_not_equal_to_non_square():
    assert Square(0, 0) != "a8"
    assert Square(0, 0) != 42


def test_equal_squares_have_same_hash():
    assert hash(Square(3, 4)) == hash(Square(3, 4))


def test_squares_usable_in_set():
    squares = {Square(0, 0), Square(0, 0), Square(1, 1)}
    assert len(squares) == 2

def test_equality_ignores_piece():
    occupied = Square(4, 4, Queen(Color.WHITE))
    empty = Square(4, 4)
    assert occupied == empty