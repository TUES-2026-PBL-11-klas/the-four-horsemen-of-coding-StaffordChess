from __future__ import annotations


class EvaluationResult:
    centipawns: int
    is_mate: bool
    mate_in_moves: int
    best_move: str
    def __init__(self, centipawns: int = 0, is_mate: bool = False,
                 mate_in_moves: int = 0, best_move: str | None = None):
        self.centipawns = centipawns
        self.is_mate = is_mate
        self.mate_in_moves = mate_in_moves
        self.best_move = best_move

    def get_advantage_in_pawns(self) -> float:
        return self.centipawns / 100

    def __repr__(self) -> str:
        if self.is_mate:
            return f"EvaluationResult(mate_in={self.mate_in_moves}, best={self.best_move})"
        return f"EvaluationResult(cp={self.centipawns}, best={self.best_move})"