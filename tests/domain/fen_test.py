import pytest

from app.domain.chess_engine import ChessEngine
from app.domain.color import Color
from app.domain.move import Move
from app.domain.piece import Pawn, King, Rook
from app.domain.fen import board_to_fen_placement

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def play(engine, s, d):
    engine.make_move(Move(engine.board.get_square(*s), engine.board.get_square(*d)))


def clear(engine):
    for r in range(8):
        for c in range(8):
            engine.board.get_square(r, c).remove_piece()



def test_starting_placement():
    placement = ChessEngine().to_fen().split()[0]
    assert placement == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"


def test_empty_board_placement():
    e = ChessEngine()
    clear(e)
    assert board_to_fen_placement(e.board) == "8/8/8/8/8/8/8/8"


def test_placement_after_e4():
    e = ChessEngine()
    play(e, (6, 4), (4, 4))
    assert e.to_fen().split()[0] == "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR"


def test_knight_is_n_not_k():
    placement = ChessEngine().to_fen().split()[0]
    assert placement.split("/")[7] == "RNBQKBNR"


def test_white_pieces_uppercase_black_lowercase():
    e = ChessEngine()
    clear(e)
    e.board.get_square(7, 0).set_piece(Rook(Color.WHITE))
    e.board.get_square(0, 0).set_piece(Rook(Color.BLACK))
    e.board.get_square(7, 4).set_piece(King(Color.WHITE))
    e.board.get_square(0, 4).set_piece(King(Color.BLACK))
    rows = e.to_fen().split()[0].split("/")
    assert rows[7][0] == "R"
    assert rows[0][0] == "r"



def test_turn_white_at_start():
    assert ChessEngine().to_fen().split()[1] == "w"


def test_turn_black_after_one_move():
    e = ChessEngine()
    play(e, (6, 4), (4, 4))
    assert e.to_fen().split()[1] == "b"


def test_turn_back_to_white_after_two_moves():
    e = ChessEngine()
    play(e, (6, 4), (4, 4))
    play(e, (1, 4), (3, 4))
    assert e.to_fen().split()[1] == "w"



def test_castling_full_at_start():
    assert ChessEngine().to_fen().split()[2] == "KQkq"


def test_castling_lost_when_white_king_moved():
    e = ChessEngine()
    e.board.get_square(7, 4).piece.has_moved = True
    rights = e.to_fen().split()[2]
    assert "K" not in rights and "Q" not in rights
    assert "k" in rights and "q" in rights


def test_castling_lost_when_kingside_rook_moved():
    e = ChessEngine()
    e.board.get_square(7, 7).piece.has_moved = True
    rights = e.to_fen().split()[2]
    assert "K" not in rights
    assert "Q" in rights


def test_castling_none_when_all_moved():
    e = ChessEngine()
    clear(e)
    for sq, piece in [((7, 4), King(Color.WHITE)), ((0, 4), King(Color.BLACK))]:
        piece.has_moved = True
        e.board.get_square(*sq).set_piece(piece)
    assert e.to_fen().split()[2] == "-"



def test_en_passant_dash_at_start():
    assert ChessEngine().to_fen().split()[3] == "-"


def test_en_passant_dash_after_e4_no_capturer():
    e = ChessEngine()
    play(e, (6, 4), (4, 4))
    assert e.to_fen().split()[3] == "-"


def test_en_passant_shown_when_capturable():
    e = ChessEngine()
    play(e, (6, 4), (4, 4))
    play(e, (1, 4), (2, 4))
    play(e, (4, 4), (3, 4))
    play(e, (1, 3), (3, 3))
    assert e.to_fen().split()[3] == "d6"


def test_en_passant_clears_next_move():
    e = ChessEngine()
    play(e, (6, 4), (4, 4))
    play(e, (1, 0), (2, 0))
    assert e.to_fen().split()[3] == "-"



def test_halfmove_always_zero():
    assert ChessEngine().to_fen().split()[4] == "0"


def test_fullmove_starts_at_one():
    assert ChessEngine().to_fen().split()[5] == "1"


def test_fullmove_increments_after_black():
    e = ChessEngine()
    play(e, (6, 4), (4, 4))
    assert e.to_fen().split()[5] == "1"
    play(e, (1, 4), (3, 4))
    assert e.to_fen().split()[5] == "2"



def test_from_fen_sets_black_turn():
    e = ChessEngine()
    e.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1")
    assert e.current_turn == Color.BLACK


def test_from_fen_places_correct_pieces():
    e = ChessEngine()
    e.from_fen("rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 0 2")
    assert e.board.get_square(5, 5).piece.get_piece_type() == "Knight"
    assert e.board.get_square(4, 4).piece.get_piece_type() == "Pawn"
    assert e.board.get_square(3, 2).piece.get_piece_type() == "Pawn"


def test_from_fen_correct_colors():
    e = ChessEngine()
    e.from_fen(STARTING_FEN)
    assert e.board.get_square(7, 4).piece.color == Color.WHITE
    assert e.board.get_square(0, 4).piece.color == Color.BLACK


def test_from_fen_clears_history():
    e = ChessEngine()
    play(e, (6, 4), (4, 4))
    e.from_fen(STARTING_FEN)
    assert e.move_history == []


def test_from_fen_empty_squares_count():
    e = ChessEngine()
    e.from_fen("8/8/8/4k3/8/4K3/4P3/8 w - - 0 1")
    count = sum(1 for r in range(8) for c in range(8)
                if e.board.get_square(r, c).piece is not None)
    assert count == 3


def test_from_fen_restores_castling_rights():
    e = ChessEngine()
    e.from_fen(STARTING_FEN)
    assert e.board.get_square(7, 4).piece.has_moved is False
    assert e.board.get_square(7, 7).piece.has_moved is False


def test_from_fen_partial_castling_rights():
    e = ChessEngine()
    e.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w K - 0 1")
    assert e.board.get_square(7, 4).piece.has_moved is False
    assert e.board.get_square(7, 7).piece.has_moved is False
    assert e.board.get_square(7, 0).piece.has_moved is True



def test_from_fen_too_few_fields_raises():
    e = ChessEngine()
    with pytest.raises(ValueError):
        e.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")


def test_from_fen_wrong_row_count_raises():
    e = ChessEngine()
    with pytest.raises(ValueError):
        e.from_fen("rnbqkbnr/pppppppp/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")


def test_from_fen_bad_column_count_raises():
    e = ChessEngine()
    with pytest.raises(ValueError):
        e.from_fen("rnbqkbn/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")



def test_pawns_can_double_move_after_load():
    e = ChessEngine()
    e.from_fen(STARTING_FEN)
    legal = e.get_all_legal_moves()
    double = [m for m in legal
              if m.start_square.algebraic_notation() == "e2"
              and m.end_square.algebraic_notation() == "e4"]
    assert len(double) == 1


def test_moved_pawn_cannot_double_after_load():
    e = ChessEngine()
    e.from_fen("rnbqkbnr/pppppppp/8/8/8/4P3/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
    e.current_turn = Color.WHITE
    legal = e.get_all_legal_moves()
    double = [m for m in legal
              if m.start_square.algebraic_notation() == "e3"
              and m.end_square.algebraic_notation() == "e5"]
    assert len(double) == 0



def test_round_trip_preserves_position():
    e = ChessEngine()
    play(e, (6, 4), (4, 4))
    play(e, (1, 2), (3, 2))
    play(e, (7, 6), (5, 5))
    fen1 = e.to_fen()

    e2 = ChessEngine()
    e2.from_fen(fen1)
    fen2 = e2.to_fen()

    assert fen1.split()[:4] == fen2.split()[:4]