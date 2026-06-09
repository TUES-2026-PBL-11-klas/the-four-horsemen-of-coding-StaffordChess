from __future__ import annotations

import chess
import chess.engine
from fastapi import HTTPException

from app.domain.evaluation_result import EvaluationResult


class AnalysisService:
    def __init__(self, stockfish_path: str, depth: int = 15, max_game_positions: int = 200):
        self.stockfish_path = stockfish_path
        self.depth = depth
        self.max_game_positions = max_game_positions

    def analyze_position(self, fen: str) -> EvaluationResult:
        try:
            board = chess.Board(fen)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid FEN: {fen}")

        try:
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                info = engine.analyse(board, chess.engine.Limit(depth=self.depth))
                return self._build_result(info)
        except FileNotFoundError:
            raise HTTPException(status_code=503, detail="Analysis engine not available")

    def analyze_game(self, fens: list[str]) -> list[EvaluationResult]:
        if len(fens) > self.max_game_positions:
            raise HTTPException(
                status_code=400,
                detail=f"Too many positions to analyse (max {self.max_game_positions})",
            )
        results = []
        try:
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                for fen in fens:
                    try:
                        board = chess.Board(fen)
                    except ValueError:
                        raise HTTPException(status_code=400, detail=f"Invalid FEN: {fen}")
                    info = engine.analyse(board, chess.engine.Limit(depth=self.depth))
                    results.append(self._build_result(info))
        except FileNotFoundError:
            raise HTTPException(status_code=503, detail="Analysis engine not available")
        return results

    def _build_result(self, info: dict) -> EvaluationResult:
        score = info["score"].white()
        best_move = None
        if "pv" in info and info["pv"]:
            best_move = info["pv"][0].uci()

        if score.is_mate():
            return EvaluationResult(
                centipawns=0, is_mate=True,
                mate_in_moves=score.mate(), best_move=best_move,
            )

        return EvaluationResult(
            centipawns=score.score(), is_mate=False,
            mate_in_moves=0, best_move=best_move,
        )