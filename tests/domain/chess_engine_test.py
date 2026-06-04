import pytest

from app.domain.chess_engine import ChessEngine
from app.domain.color import Color
from app.domain.game_result import GameResult
from app.domain.move import Move
from app.domain.piece import (
    Pawn, Rook, Knight, Bishop, Queen, King,
)



def clear_board(engine):
    for r in range(8):
        for c in range(8):
            engine.board.get_square(r, c).remove_piece()


def play_move(engine, start_rc, end_rc):
    start = engine.board.get_square(*start_rc)
    end = engine.board.get_square(*end_rc)
    engine.make_move(Move(start, end))



def test_initial_turn_is_white():
    assert ChessEngine().current_turn == Color.WHITE


def test_initial_history_empty():
    assert ChessEngine().move_history == []


def test_initial_game_not_over():
    assert ChessEngine().game_result.is_game_over() is False


def test_initial_no_draw_request():
    assert ChessEngine().draw_requested_by is None


def test_initial_position_has_20_legal_moves():
    assert len(ChessEngine().get_all_legal_moves()) == 20


def test_initial_not_in_check():
    e = ChessEngine()
    assert e.is_in_check(Color.WHITE) is False
    assert e.is_in_check(Color.BLACK) is False



def test_make_move_moves_piece():
    e = ChessEngine()
    play_move(e, (6, 4), (4, 4))
    assert e.board.get_square(6, 4).piece is None
    assert e.board.get_square(4, 4).piece is not None


def test_make_move_switches_turn():
    e = ChessEngine()
    play_move(e, (6, 4), (4, 4))
    assert e.current_turn == Color.BLACK


def test_make_move_adds_to_history():
    e = ChessEngine()
    play_move(e, (6, 4), (4, 4))
    assert len(e.move_history) == 1


def test_make_move_sets_has_moved():
    e = ChessEngine()
    pawn = e.board.get_square(6, 4).piece
    play_move(e, (6, 4), (4, 4))
    assert pawn.has_moved is True


def test_undo_restores_position():
    e = ChessEngine()
    play_move(e, (6, 4), (4, 4))
    e.undo_move()
    assert e.board.get_square(6, 4).piece is not None
    assert e.board.get_square(4, 4).piece is None


def test_undo_restores_turn():
    e = ChessEngine()
    play_move(e, (6, 4), (4, 4))
    e.undo_move()
    assert e.current_turn == Color.WHITE


def test_undo_restores_history():
    e = ChessEngine()
    play_move(e, (6, 4), (4, 4))
    e.undo_move()
    assert len(e.move_history) == 0


def test_undo_restores_has_moved():
    e = ChessEngine()
    pawn = e.board.get_square(6, 4).piece
    play_move(e, (6, 4), (4, 4))
    e.undo_move()
    assert pawn.has_moved is False


def test_undo_empty_history_does_nothing():
    e = ChessEngine()
    e.undo_move()
    assert e.current_turn == Color.WHITE



def test_capture_replaces_piece():
    e = ChessEngine()
    black_pawn = Pawn(Color.BLACK)
    e.board.get_square(4, 4).set_piece(black_pawn)
    play_move(e, (6, 4), (4, 4))
    assert e.board.get_square(4, 4).piece.color == Color.WHITE


def test_undo_capture_restores_captured_piece():
    e = ChessEngine()
    black_pawn = Pawn(Color.BLACK)
    e.board.get_square(4, 4).set_piece(black_pawn)
    play_move(e, (6, 4), (4, 4))
    e.undo_move()
    assert e.board.get_square(4, 4).piece is black_pawn



def test_find_white_king():
    e = ChessEngine()
    king_sq = e.find_king(Color.WHITE)
    assert king_sq.x == 7 and king_sq.y == 4


def test_find_black_king():
    e = ChessEngine()
    king_sq = e.find_king(Color.BLACK)
    assert king_sq.x == 0 and king_sq.y == 4

def test_find_king_raises_when_missing():
    e = ChessEngine()
    clear_board(e)
    with pytest.raises(ValueError):
        e.find_king(Color.WHITE)


def test_square_under_attack_by_rook():
    e = ChessEngine()
    clear_board(e)
    e.board.get_square(4, 0).set_piece(Rook(Color.WHITE)) 
    assert e.is_square_under_attack(4, 5, Color.WHITE) is True
    assert e.is_square_under_attack(0, 0, Color.WHITE) is True

def test_square_not_under_attack():
    e = ChessEngine()
    clear_board(e)
    e.board.get_square(4, 0).set_piece(Rook(Color.WHITE))
    assert e.is_square_under_attack(5, 1, Color.WHITE) is False


def test_attack_blocked_by_piece():
    e = ChessEngine()
    clear_board(e)
    e.board.get_square(4, 0).set_piece(Rook(Color.WHITE))   
    e.board.get_square(4, 3).set_piece(Pawn(Color.WHITE))
    assert e.is_square_under_attack(4, 5, Color.WHITE) is False
    assert e.is_square_under_attack(4, 1, Color.WHITE) is True



def test_king_in_check_from_rook():
    e = ChessEngine()
    clear_board(e)
    e.board.get_square(7, 4).set_piece(King(Color.WHITE))
    e.board.get_square(0, 4).set_piece(King(Color.BLACK))
    e.board.get_square(4, 4).set_piece(Rook(Color.BLACK))
    assert e.is_in_check(Color.WHITE) is True


def test_king_not_in_check():
    e = ChessEngine()
    clear_board(e)
    e.board.get_square(7, 4).set_piece(King(Color.WHITE))
    e.board.get_square(0, 4).set_piece(King(Color.BLACK))
    e.board.get_square(4, 3).set_piece(Rook(Color.BLACK))
    assert e.is_in_check(Color.WHITE) is False



def test_pinned_piece_cannot_move():
    e = ChessEngine()
    clear_board(e)
    e.board.get_square(7, 4).set_piece(King(Color.WHITE))
    e.board.get_square(6, 4).set_piece(Bishop(Color.WHITE))
    e.board.get_square(0, 4).set_piece(Rook(Color.BLACK))
    e.board.get_square(0, 0).set_piece(King(Color.BLACK))
    e.current_turn = Color.WHITE
    legal = e.get_all_legal_moves()
    bishop_moves = [m for m in legal if m.piece_moved.get_piece_type() == "Bishop"]
    assert len(bishop_moves) == 0


def test_unpinned_piece_can_move():
    e = ChessEngine()
    clear_board(e)
    e.board.get_square(7, 4).set_piece(King(Color.WHITE))
    e.board.get_square(6, 4).set_piece(Bishop(Color.WHITE))
    e.board.get_square(0, 0).set_piece(King(Color.BLACK))
    e.current_turn = Color.WHITE
    legal = e.get_all_legal_moves()
    bishop_moves = [m for m in legal if m.piece_moved.get_piece_type() == "Bishop"]
    assert len(bishop_moves) > 0



def test_fools_mate():
    e = ChessEngine()
    play_move(e, (6, 5), (5, 5))
    play_move(e, (1, 4), (3, 4))
    play_move(e, (6, 6), (4, 6))
    play_move(e, (0, 3), (4, 7))
    assert e.current_turn == Color.WHITE
    assert e.is_in_check(Color.WHITE) is True
    assert e.is_checkmate() is True
    assert len(e.get_all_legal_moves()) == 0


def test_scholars_mate():
    e = ChessEngine()
    play_move(e, (6, 4), (4, 4))
    play_move(e, (1, 4), (3, 4))
    play_move(e, (7, 5), (4, 2))
    play_move(e, (0, 1), (2, 2))
    play_move(e, (7, 3), (3, 7))
    play_move(e, (0, 6), (2, 5))
    play_move(e, (3, 7), (1, 5))
    assert e.is_checkmate() is True


def test_no_false_mate_midgame():
    e = ChessEngine()
    play_move(e, (6, 4), (4, 4))
    play_move(e, (1, 4), (3, 4))
    play_move(e, (7, 5), (4, 2))
    play_move(e, (0, 1), (2, 2))
    play_move(e, (7, 3), (3, 7))
    assert e.is_checkmate() is False



def test_stalemate():
    e = ChessEngine()
    clear_board(e)
    e.board.get_square(0, 7).set_piece(King(Color.BLACK))
    e.board.get_square(1, 5).set_piece(Queen(Color.WHITE))
    e.board.get_square(2, 6).set_piece(King(Color.WHITE))
    e.current_turn = Color.BLACK
    assert e.is_in_check(Color.BLACK) is False
    assert len(e.get_all_legal_moves()) == 0
    assert e.is_stalemate() is True
    assert e.is_checkmate() is False


def test_checkmate_is_not_stalemate():
    e = ChessEngine()
    play_move(e, (6, 5), (5, 5))
    play_move(e, (1, 4), (3, 4))
    play_move(e, (6, 6), (4, 6))
    play_move(e, (0, 3), (4, 7))
    assert e.is_stalemate() is False



def setup_kingside_castle(e):
    play_move(e, (7, 6), (5, 5))
    play_move(e, (1, 4), (2, 4))
    play_move(e, (6, 4), (4, 4))
    play_move(e, (2, 4), (3, 4))
    play_move(e, (7, 5), (6, 4))
    play_move(e, (1, 0), (2, 0))


def test_kingside_castle_available():
    e = ChessEngine()
    setup_kingside_castle(e)
    castles = [m for m in e.get_all_legal_moves() if m.is_king_castling]
    assert len(castles) == 1


def test_kingside_castle_moves_king_and_rook():
    e = ChessEngine()
    setup_kingside_castle(e)
    castle = [m for m in e.get_all_legal_moves() if m.is_king_castling][0]
    e.make_move(castle)
    assert e.board.get_square(7, 6).piece.get_piece_type() == "King"
    assert e.board.get_square(7, 5).piece.get_piece_type() == "Rook"


def test_undo_kingside_castle():
    e = ChessEngine()
    setup_kingside_castle(e)
    castle = [m for m in e.get_all_legal_moves() if m.is_king_castling][0]
    e.make_move(castle)
    e.undo_move()
    assert e.board.get_square(7, 4).piece.get_piece_type() == "King"
    assert e.board.get_square(7, 7).piece.get_piece_type() == "Rook"
    assert e.board.get_square(7, 6).piece is None


def test_cannot_castle_through_check():
    e = ChessEngine()
    clear_board(e)
    e.board.get_square(7, 4).set_piece(King(Color.WHITE))
    e.board.get_square(7, 7).set_piece(Rook(Color.WHITE))
    e.board.get_square(0, 4).set_piece(King(Color.BLACK))
    e.board.get_square(0, 5).set_piece(Rook(Color.BLACK))
    e.current_turn = Color.WHITE
    castles = [m for m in e.get_all_legal_moves() if m.is_king_castling]
    assert len(castles) == 0


def test_cannot_castle_while_in_check():
    e = ChessEngine()
    clear_board(e)
    e.board.get_square(7, 4).set_piece(King(Color.WHITE))
    e.board.get_square(7, 7).set_piece(Rook(Color.WHITE))
    e.board.get_square(0, 4).set_piece(King(Color.BLACK))
    e.board.get_square(0, 4).remove_piece()
    e.board.get_square(1, 4).set_piece(King(Color.BLACK))
    e.board.get_square(6, 4).set_piece(Rook(Color.BLACK))
    e.current_turn = Color.WHITE
    castles = [m for m in e.get_all_legal_moves() if m.is_king_castling]
    assert len(castles) == 0


def test_cannot_castle_after_king_moved():
    e = ChessEngine()
    clear_board(e)
    king = King(Color.WHITE)
    king.has_moved = True
    e.board.get_square(7, 4).set_piece(king)
    e.board.get_square(7, 7).set_piece(Rook(Color.WHITE))
    e.board.get_square(0, 0).set_piece(King(Color.BLACK))
    e.current_turn = Color.WHITE
    castles = [m for m in e.get_all_legal_moves() if m.is_king_castling]
    assert len(castles) == 0



def setup_en_passant(e):
    play_move(e, (6, 4), (4, 4))
    play_move(e, (1, 0), (2, 0))
    play_move(e, (4, 4), (3, 4))
    play_move(e, (1, 3), (3, 3))


def test_en_passant_available():
    e = ChessEngine()
    setup_en_passant(e)
    ep = [m for m in e.get_all_legal_moves() if m.is_en_passant]
    assert len(ep) == 1


def test_en_passant_target_square():
    e = ChessEngine()
    setup_en_passant(e)
    ep = [m for m in e.get_all_legal_moves() if m.is_en_passant][0]
    assert ep.end_square.algebraic_notation() == "d6"


def test_en_passant_captures_pawn():
    e = ChessEngine()
    setup_en_passant(e)
    ep = [m for m in e.get_all_legal_moves() if m.is_en_passant][0]
    e.make_move(ep)
    assert e.board.get_square(2, 3).piece is not None
    assert e.board.get_square(3, 3).piece is None


def test_undo_en_passant():
    e = ChessEngine()
    setup_en_passant(e)
    ep = [m for m in e.get_all_legal_moves() if m.is_en_passant][0]
    e.make_move(ep)
    e.undo_move()
    assert e.board.get_square(3, 4).piece is not None
    assert e.board.get_square(3, 3).piece is not None
    assert e.board.get_square(2, 3).piece is None



def setup_promotion(e):
    clear_board(e)
    pawn = Pawn(Color.WHITE)
    pawn.has_moved = True
    e.board.get_square(1, 0).set_piece(pawn)
    e.board.get_square(7, 4).set_piece(King(Color.WHITE))
    e.board.get_square(0, 7).set_piece(King(Color.BLACK))
    e.current_turn = Color.WHITE


def test_promotion_offers_four_pieces():
    e = ChessEngine()
    setup_promotion(e)
    promos = [m for m in e.get_all_legal_moves() if m.is_pawn_promotion]
    assert len(promos) == 4


def test_promotion_piece_types():
    e = ChessEngine()
    setup_promotion(e)
    promos = [m for m in e.get_all_legal_moves() if m.is_pawn_promotion]
    types = sorted(m.promotion_piece.get_piece_type() for m in promos)
    assert types == ["Bishop", "Knight", "Queen", "Rook"]


def test_promotion_to_queen():
    e = ChessEngine()
    setup_promotion(e)
    promos = [m for m in e.get_all_legal_moves() if m.is_pawn_promotion]
    queen_promo = [m for m in promos if m.promotion_piece.get_piece_type() == "Queen"][0]
    e.make_move(queen_promo)
    assert e.board.get_square(0, 0).piece.get_piece_type() == "Queen"
    assert e.board.get_square(1, 0).piece is None


def test_undo_promotion():
    e = ChessEngine()
    setup_promotion(e)
    promos = [m for m in e.get_all_legal_moves() if m.is_pawn_promotion]
    queen_promo = [m for m in promos if m.promotion_piece.get_piece_type() == "Queen"][0]
    e.make_move(queen_promo)
    e.undo_move()
    assert e.board.get_square(1, 0).piece.get_piece_type() == "Pawn"
    assert e.board.get_square(0, 0).piece is None



def test_white_resigns():
    e = ChessEngine()
    e.resign()
    assert e.game_result.result == GameResult.Result.WHITE_RESIGNS
    assert e.game_result.is_game_over() is True


def test_black_resigns():
    e = ChessEngine()
    e.current_turn = Color.BLACK
    e.resign()
    assert e.game_result.result == GameResult.Result.BLACK_RESIGNS



def test_draw_request_pending():
    e = ChessEngine()
    accepted = e.request_draw()
    assert accepted is False
    assert e.draw_requested_by == Color.WHITE


def test_draw_request_same_play_moveer_again():
    e = ChessEngine()
    e.request_draw()
    accepted = e.request_draw()
    assert accepted is False


def test_draw_accepted_by_opponent():
    e = ChessEngine()
    e.request_draw()
    e.current_turn = Color.BLACK
    accepted = e.request_draw()
    assert accepted is True
    assert e.game_result.result == GameResult.Result.DRAW


def test_accept_draw():
    e = ChessEngine()
    e.request_draw()
    e.current_turn = Color.BLACK
    e.accept_draw()
    assert e.game_result.result == GameResult.Result.DRAW
    assert e.draw_requested_by is None


def test_accept_draw_no_request_raises():
    e = ChessEngine()
    with pytest.raises(ValueError):
        e.accept_draw()


def test_accept_own_draw_raises():
    e = ChessEngine()
    e.request_draw()
    with pytest.raises(ValueError):
        e.accept_draw()


def test_decline_draw():
    e = ChessEngine()
    e.request_draw()
    e.current_turn = Color.BLACK
    e.decline_draw()
    assert e.draw_requested_by is None
    assert e.game_result.is_game_over() is False


def test_decline_draw_no_request_raises():
    e = ChessEngine()
    with pytest.raises(ValueError):
        e.decline_draw()


def test_clear_draw_request():
    e = ChessEngine()
    e.request_draw()
    e.clear_draw_request()
    assert e.draw_requested_by is None