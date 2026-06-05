import pytest

from app.domain.color import Color
from app.domain.board import Board
from app.domain.move import Move
from app.domain.square import Square
from app.domain.piece import Pawn, Knight, Queen


def make_board():
    return Board()



def test_move_stores_squares():
    board = make_board()
    start = board.get_square(6, 4)
    end = board.get_square(4, 4)
    move = Move(start, end)
    assert move.start_square is start
    assert move.end_square is end


def test_move_records_piece_moved():
    board = make_board()
    start = board.get_square(6, 4)
    move = Move(start, board.get_square(4, 4))
    assert move.piece_moved is start.piece
    assert isinstance(move.piece_moved, Pawn)


def test_move_records_captured_piece_when_present():
    board = make_board()
    board.get_square(4, 4).set_piece(Pawn(Color.BLACK))
    captured = board.get_square(4, 4).piece
    move = Move(board.get_square(6, 4), board.get_square(4, 4))
    assert move.piece_captured is captured


def test_move_no_capture_on_empty_target():
    board = make_board()
    move = Move(board.get_square(6, 4), board.get_square(4, 4))
    assert move.piece_captured is None


def test_move_records_has_piece_moved():
    board = make_board()
    move = Move(board.get_square(6, 4), board.get_square(4, 4))
    assert move.has_piece_moved is False


def test_move_default_flags_false():
    board = make_board()
    move = Move(board.get_square(6, 4), board.get_square(4, 4))
    assert move.is_en_passant is False
    assert move.is_pawn_promotion is False
    assert move.is_king_castling is False
    assert move.is_queen_castling is False
    assert move.promotion_piece is None
    assert move.en_passant_captured_square is None



def test_move_from_empty_square_raises():
    board = make_board()
    empty = board.get_square(4, 4)
    target = board.get_square(4, 5)
    with pytest.raises(ValueError):
        Move(empty, target)


def test_move_same_start_and_end_raises():
    board = make_board()
    sq = board.get_square(6, 4)
    same = board.get_square(6, 4)
    with pytest.raises(ValueError):
        Move(sq, same)



def test_copy_preserves_all_fields():
    board = make_board()
    original = Move(board.get_square(6, 4), board.get_square(4, 4))
    original.is_pawn_promotion = True
    original.promotion_piece = Queen(Color.WHITE)

    copy = Move.copy_of(original)
    assert copy.start_square == original.start_square
    assert copy.end_square == original.end_square
    assert copy.piece_moved is original.piece_moved
    assert copy.is_pawn_promotion == original.is_pawn_promotion
    assert copy.promotion_piece is original.promotion_piece


def test_copy_is_different_object():
    board = make_board()
    original = Move(board.get_square(6, 4), board.get_square(4, 4))
    copy = Move.copy_of(original)
    assert copy is not original


def test_copy_does_not_validate():
    board = make_board()
    original = Move(board.get_square(6, 4), board.get_square(4, 4))
    copy = Move.copy_of(original)
    assert copy is not None



def test_equal_moves():
    board = make_board()
    m1 = Move(board.get_square(6, 4), board.get_square(4, 4))
    m2 = Move(board.get_square(6, 4), board.get_square(4, 4))
    assert m1.are_two_moves_equal(m2) is True


def test_different_end_not_equal():
    board = make_board()
    m1 = Move(board.get_square(6, 4), board.get_square(4, 4))
    m2 = Move(board.get_square(6, 4), board.get_square(5, 4))
    assert m1.are_two_moves_equal(m2) is False


def test_different_start_not_equal():
    board = make_board()
    m1 = Move(board.get_square(6, 4), board.get_square(4, 4))
    m2 = Move(board.get_square(6, 3), board.get_square(4, 3))
    assert m1.are_two_moves_equal(m2) is False


def test_move_not_equal_to_non_move():
    board = make_board()
    m1 = Move(board.get_square(6, 4), board.get_square(4, 4))
    assert m1.are_two_moves_equal("e4") is False



def test_notation_pawn_move():
    board = make_board()
    move = Move(board.get_square(6, 4), board.get_square(4, 4))
    assert move.get_move_in_notation() == "e4"


def test_notation_knight_move():
    board = make_board()
    move = Move(board.get_square(7, 1), board.get_square(5, 2))
    assert move.get_move_in_notation() == "Nc3"


def test_notation_king_castling():
    board = make_board()
    move = Move(board.get_square(7, 4), board.get_square(7, 6))
    move.is_king_castling = True
    assert move.get_move_in_notation() == "O-O"


def test_notation_queen_castling():
    board = make_board()
    move = Move(board.get_square(7, 4), board.get_square(7, 2))
    move.is_queen_castling = True
    assert move.get_move_in_notation() == "O-O-O"


def test_notation_capture():
    board = make_board()
    board.get_square(5, 2).set_piece(Pawn(Color.BLACK))
    move = Move(board.get_square(7, 1), board.get_square(5, 2))
    assert move.get_move_in_notation() == "Nxc3"


def test_notation_pawn_capture_uses_file():
    board = make_board()
    board.get_square(5, 4).set_piece(Pawn(Color.BLACK))
    move = Move(board.get_square(6, 3), board.get_square(5, 4))
    assert move.get_move_in_notation() == "dxe3"