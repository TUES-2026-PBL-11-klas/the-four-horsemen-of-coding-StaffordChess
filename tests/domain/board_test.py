import pytest

from app.domain.color import Color
from app.domain.board import Board
from app.domain.piece import (
    Pawn, Rook, Knight, Bishop, Queen, King,
)



def test_board_has_64_squares():
    board = Board()
    count = sum(1 for row in board.squares for sq in row if sq is not None)
    assert count == 64


def test_board_is_8x8():
    board = Board()
    assert len(board.squares) == 8
    for row in board.squares:
        assert len(row) == 8


def test_each_square_knows_its_coords():
    board = Board()
    for x in range(8):
        for y in range(8):
            sq = board.get_square(x, y)
            assert sq.x == x
            assert sq.y == y



def test_white_pawns_on_row_6():
    board = Board()
    for col in range(8):
        piece = board.get_square(6, col).piece
        assert isinstance(piece, Pawn)
        assert piece.color == Color.WHITE


def test_black_pawns_on_row_1():
    board = Board()
    for col in range(8):
        piece = board.get_square(1, col).piece
        assert isinstance(piece, Pawn)
        assert piece.color == Color.BLACK



@pytest.mark.parametrize("col,piece_type", [
    (0, Rook), (1, Knight), (2, Bishop), (3, Queen),
    (4, King), (5, Bishop), (6, Knight), (7, Rook),
])
def test_white_back_rank(col, piece_type):
    board = Board()
    piece = board.get_square(7, col).piece
    assert isinstance(piece, piece_type)
    assert piece.color == Color.WHITE


@pytest.mark.parametrize("col,piece_type", [
    (0, Rook), (1, Knight), (2, Bishop), (3, Queen),
    (4, King), (5, Bishop), (6, Knight), (7, Rook),
])
def test_black_back_rank(col, piece_type):
    board = Board()
    piece = board.get_square(0, col).piece
    assert isinstance(piece, piece_type)
    assert piece.color == Color.BLACK


def test_kings_and_queens_on_correct_files():
    board = Board()
    assert isinstance(board.get_square(7, 3).piece, Queen)
    assert isinstance(board.get_square(7, 4).piece, King)
    assert isinstance(board.get_square(0, 3).piece, Queen)
    assert isinstance(board.get_square(0, 4).piece, King)



def test_middle_rows_empty():
    board = Board()
    for row in (2, 3, 4, 5):
        for col in range(8):
            assert board.get_square(row, col).piece is None



def test_two_boards_are_independent():
    board1 = Board()
    board2 = Board()
    board1.get_square(4, 4).set_piece(Queen(Color.WHITE))
    assert board2.get_square(4, 4).piece is None


def test_modifying_one_board_does_not_affect_other():
    board1 = Board()
    board2 = Board()
    board1.get_square(6, 0).remove_piece()
    assert board2.get_square(6, 0).piece is not None



def test_get_square_valid():
    board = Board()
    sq = board.get_square(4, 4)
    assert sq.x == 4 and sq.y == 4


@pytest.mark.parametrize("x,y", [
    (-1, 0), (8, 0), (0, -1), (0, 8), (10, 10),
])
def test_get_square_out_of_bounds_raises(x, y):
    board = Board()
    with pytest.raises(ValueError):
        board.get_square(x, y)



def test_get_square_by_algebraic_e1_is_white_king():
    board = Board()
    sq = board.get_square_by_algebraic_notation("e1")
    assert isinstance(sq.piece, King)
    assert sq.piece.color == Color.WHITE


def test_get_square_by_algebraic_d8_is_black_queen():
    board = Board()
    sq = board.get_square_by_algebraic_notation("d8")
    assert isinstance(sq.piece, Queen)
    assert sq.piece.color == Color.BLACK


def test_get_square_by_algebraic_a1():
    board = Board()
    sq = board.get_square_by_algebraic_notation("a1")
    assert sq.x == 7 and sq.y == 0


@pytest.mark.parametrize("bad", ["e", "e11", "", "z1", "e9", "a0"])
def test_get_square_by_algebraic_invalid_raises(bad):
    board = Board()
    with pytest.raises(ValueError):
        board.get_square_by_algebraic_notation(bad)



def test_algebraic_matches_coordinate_access():
    board = Board()
    by_coord = board.get_square(7, 4)       # e1
    by_algebra = board.get_square_by_algebraic_notation("e1")
    assert by_coord is by_algebra