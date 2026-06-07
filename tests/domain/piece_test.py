import pytest

from app.domain.color import Color
from app.domain.piece import (
    Piece, Pawn, Rook, Knight, Bishop, Queen, King,
)


def targets(piece, position):
    return set(piece.get_possible_moves(position))



def test_piece_is_abstract():
    with pytest.raises(TypeError):
        Piece(Color.WHITE)


def test_piece_starts_unmoved():
    assert Pawn(Color.WHITE).has_moved is False


def test_piece_stores_color():
    assert Pawn(Color.BLACK).color == Color.BLACK


def test_get_piece_type():
    assert Pawn(Color.WHITE).get_piece_type() == "Pawn"
    assert King(Color.WHITE).get_piece_type() == "King"


@pytest.mark.parametrize("piece_cls,symbol", [
    (Pawn, "P"), (Knight, "N"), (Bishop, "B"),
    (Rook, "R"), (Queen, "Q"), (King, "K"),
])
def test_piece_symbols(piece_cls, symbol):
    assert piece_cls(Color.WHITE).get_piece_symbol() == symbol


def test_knight_symbol_is_n_not_k():
    assert Knight(Color.WHITE).get_piece_symbol() == "N"
    assert King(Color.WHITE).get_piece_symbol() == "K"



def test_white_pawn_unmoved_forward_and_double():
    pawn = Pawn(Color.WHITE)
    moves = targets(pawn, (6, 4))
    assert (5, 4) in moves
    assert (4, 4) in moves


def test_black_pawn_unmoved_forward_and_double():
    pawn = Pawn(Color.BLACK)
    moves = targets(pawn, (1, 4))
    assert (2, 4) in moves
    assert (3, 4) in moves


def test_pawn_moved_no_double():
    pawn = Pawn(Color.WHITE)
    pawn.has_moved = True
    moves = targets(pawn, (5, 4))
    assert (4, 4) in moves
    assert (3, 4) not in moves

def test_white_pawn_includes_diagonals():
    pawn = Pawn(Color.WHITE)
    moves = targets(pawn, (6, 4))
    assert (5, 3) in moves
    assert (5, 5) in moves


def test_pawn_diagonal_at_edge_only_one_side():
    pawn = Pawn(Color.WHITE)
    moves = targets(pawn, (6, 0))
    assert (5, 1) in moves
    assert (5, -1) not in moves


def test_white_pawn_direction_upward():
    pawn = Pawn(Color.WHITE)
    moves = targets(pawn, (4, 4))
    assert (3, 4) in moves
    assert (5, 4) not in moves


def test_knight_center_8_moves():
    assert len(targets(Knight(Color.WHITE), (4, 4))) == 8


def test_knight_center_exact_squares():
    moves = targets(Knight(Color.WHITE), (4, 4))
    expected = {(6, 5), (6, 3), (2, 5), (2, 3),
                (5, 6), (5, 2), (3, 6), (3, 2)}
    assert moves == expected


def test_knight_corner_2_moves():
    assert len(targets(Knight(Color.WHITE), (0, 0))) == 2


def test_knight_corner_exact_squares():
    moves = targets(Knight(Color.WHITE), (0, 0))
    assert moves == {(2, 1), (1, 2)}


def test_knight_does_not_slide():
    moves = targets(Knight(Color.WHITE), (4, 4))
    assert (6, 6) not in moves
    assert (0, 4) not in moves


def test_knight_edge_4_moves():
    moves = targets(Knight(Color.WHITE), (0, 4))  # e8
    assert len(moves) == 4


def test_knight_color_does_not_affect_moves():
    white_moves = targets(Knight(Color.WHITE), (4, 4))
    black_moves = targets(Knight(Color.BLACK), (4, 4))
    assert white_moves == black_moves



def test_rook_center_14_moves():
    assert len(targets(Rook(Color.WHITE), (4, 4))) == 14


def test_rook_corner_14_moves():
    assert len(targets(Rook(Color.WHITE), (0, 0))) == 14


def test_rook_moves_horizontally_and_vertically():
    moves = targets(Rook(Color.WHITE), (4, 4))
    assert (4, 0, 0, -1) in moves
    assert (4, 7, 0, 1) in moves
    assert (0, 4, -1, 0) in moves
    assert (7, 4, 1, 0) in moves


def test_rook_no_diagonal():
    moves = targets(Rook(Color.WHITE), (4, 4))
    assert (5, 5, 1, 1) not in moves
    assert (3, 3, -1, -1) not in moves


def test_rook_stays_on_board():
    moves = targets(Rook(Color.WHITE), (4, 4))
    for r, c , dr, dc in moves:
        assert 0 <= r < 8 and 0 <= c < 8



def test_bishop_center_13_moves():
    assert len(targets(Bishop(Color.WHITE), (4, 4))) == 13


def test_bishop_corner_7_moves():
    assert len(targets(Bishop(Color.WHITE), (0, 0))) == 7


def test_bishop_moves_diagonally():
    moves = targets(Bishop(Color.WHITE), (4, 4))
    assert (5, 5, 1, 1) in moves
    assert (3, 3, -1, -1) in moves
    assert (5, 3, 1, -1) in moves
    assert (3, 5, -1, 1) in moves


def test_bishop_no_straight():
    moves = targets(Bishop(Color.WHITE), (4, 4))
    assert (4, 5, 0, 1) not in moves
    assert (5, 4, 1, 0) not in moves


def test_bishop_stays_on_color():
    moves = targets(Bishop(Color.WHITE), (4, 4))
    for r, c , dr, dc in moves:
        assert (r + c) % 2 == 0



def test_queen_center_27_moves():
    assert len(targets(Queen(Color.WHITE), (4, 4))) == 27


def test_queen_corner_21_moves():
    assert len(targets(Queen(Color.WHITE), (0, 0))) == 21


def test_queen_combines_rook_and_bishop():
    queen_moves = targets(Queen(Color.WHITE), (4, 4))
    rook_moves = targets(Rook(Color.WHITE), (4, 4))
    bishop_moves = targets(Bishop(Color.WHITE), (4, 4))
    assert queen_moves == rook_moves | bishop_moves



def test_king_center_8_moves():
    assert len(targets(King(Color.WHITE), (4, 4))) == 8


def test_king_corner_3_moves():
    assert len(targets(King(Color.WHITE), (0, 0))) == 3


def test_king_edge_5_moves():
    assert len(targets(King(Color.WHITE), (0, 4))) == 5


def test_king_moves_one_square_all_directions():
    moves = targets(King(Color.WHITE), (4, 4))
    expected = {(3, 3), (3, 4), (3, 5),
                (4, 3),         (4, 5),
                (5, 3), (5, 4), (5, 5)}
    assert moves == expected


def test_king_does_not_slide():
    moves = targets(King(Color.WHITE), (4, 4))
    assert (6, 6) not in moves
    assert (4, 7) not in moves


def test_king_stays_on_board():
    moves = targets(King(Color.WHITE), (0, 0))
    for r, c in moves:
        assert 0 <= r < 8 and 0 <= c < 8