from __future__ import annotations

from app.domain.board import Board
from app.domain.color import Color
from app.domain.piece import (
    Bishop, King, Knight, Pawn, Queen, Rook,
)

_LETTER_TO_PIECE = {
    "p": Pawn,
    "n": Knight,
    "b": Bishop,
    "r": Rook,
    "q": Queen,
    "k": King,
}


def _piece_to_letter(piece) -> str:
    type_name = piece.get_piece_type()
    if type_name == "Knight":
        letter = "n"
    else:
        letter = type_name[0].lower()
    return letter.upper() if piece.color == Color.WHITE else letter


def board_to_fen_placement(board: Board) -> str:
    rows = []
    for row in range(8):
        fen_row = ""
        empty_count = 0
        for col in range(8):
            piece = board.get_square(row, col).piece
            if piece is None:
                empty_count += 1
            else:
                if empty_count > 0:
                    fen_row += str(empty_count)
                    empty_count = 0
                fen_row += _piece_to_letter(piece)
        if empty_count > 0:
            fen_row += str(empty_count)
        rows.append(fen_row)
    return "/".join(rows)

def _can_castle(board, king_row, rook_col):
        king_sq = board.get_square(king_row, 4)
        rook_sq = board.get_square(king_row, rook_col)
        king = king_sq.piece
        rook = rook_sq.piece
        if king is None or king.get_piece_type() != "King" or king.has_moved:
            return False
        if rook is None or rook.get_piece_type() != "Rook" or rook.has_moved:
            return False
        return True

def get_castling_rights(engine) -> str:
    rights = ""
    board = engine.board

    if _can_castle(board, 7, 7):
        rights += "K"
    if _can_castle(board, 7, 0):
        rights += "Q"
    if _can_castle(board, 0, 7):
        rights += "k"
    if _can_castle(board, 0, 0):
        rights += "q"

    return rights if rights else "-"


def get_en_passant_target_squares(engine) -> str:
    en_passant_moves = engine.get_en_passant_moves()
    if not en_passant_moves:
        return "-"

    return en_passant_moves[0].end_square.algebraic_notation()


def load_to_fen(engine) -> str:
    placement = board_to_fen_placement(engine.board)
    active = "w" if engine.current_turn == Color.WHITE else "b"
    castling = get_castling_rights(engine)
    en_passant = get_en_passant_target_squares(engine)
    halfmove = "0"
    fullmove = str(len(engine.move_history) // 2 + 1)

    return f"{placement} {active} {castling} {en_passant} {halfmove} {fullmove}"


def _create_piece(letter: str):
    color = Color.WHITE if letter.isupper() else Color.BLACK
    piece_cls = _LETTER_TO_PIECE[letter.lower()]
    return piece_cls(color)


def _set_has_moved_flag(piece, row: int, col: int) -> None:
    if piece.get_piece_type() == "Pawn":
        starting_row = 6 if piece.color == Color.WHITE else 1
        piece.has_moved = (row != starting_row)
    else:
        piece.has_moved = True


def load_from_fen(engine, fen: str) -> None:

    parts = fen.strip().split()
    if len(parts) < 4:
        raise ValueError("FEN must have at least 4 fields (placement, turn, castling, en passant).")

    placement = parts[0]
    active = parts[1]
    castling = parts[2]

    rows = placement.split("/")
    if len(rows) != 8:
        raise ValueError("FEN placement must have 8 rows separated by '/'.")

    new_board = Board()
    for row in range(8):
        for col in range(8):
            new_board.get_square(row, col).remove_piece()

    for row in range(8):
        col = 0
        for char in rows[row]:
            if char.isdigit():
                col += int(char)
            else:
                piece = _create_piece(char)
                _set_has_moved_flag(piece, row, col)
                new_board.get_square(row, col).set_piece(piece)
                col += 1
        if col != 8:
            raise ValueError(f"FEN row {row} does not describe exactly 8 columns.")

    engine.board = new_board
    engine.current_turn = Color.WHITE if active == "w" else Color.BLACK
    engine.move_history = []

    _apply_castling_rights(engine, castling)




def _unmark_moved(board, king_row, rook_col):
        king = board.get_square(king_row, 4).piece
        rook = board.get_square(king_row, rook_col).piece
        if king is not None and king.get_piece_type() == "King":
            king.has_moved = False
        if rook is not None and rook.get_piece_type() == "Rook":
            rook.has_moved = False

def _apply_castling_rights(engine, castling: str) -> None:
    board = engine.board
    if castling == "-":
        return
    if "K" in castling:
        _unmark_moved(board, 7, 7)
    if "Q" in castling:
        _unmark_moved(board, 7, 0)
    if "k" in castling:
        _unmark_moved(board, 0, 7)
    if "q" in castling:
        _unmark_moved(board, 0, 0)