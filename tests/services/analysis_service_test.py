import pytest
from unittest.mock import patch, MagicMock
import chess
import chess.engine
from fastapi import HTTPException

from app.services.analysis_service import AnalysisService
from app.domain.evaluation_result import EvaluationResult


START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def make_engine_with_score(score, pv_move="e2e4"):
    engine = MagicMock()
    engine.analyse.return_value = {
        "score": score,
        "pv": [chess.Move.from_uci(pv_move)] if pv_move else [],
    }
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=engine)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def test_analyze_position_centipawns():
    score = chess.engine.PovScore(chess.engine.Cp(150), chess.WHITE)
    with patch("chess.engine.SimpleEngine.popen_uci",
               return_value=make_engine_with_score(score)):
        service = AnalysisService("fake_path")
        result = service.analyze_position(START_FEN)
    assert isinstance(result, EvaluationResult)
    assert result.centipawns == 150
    assert result.is_mate is False
    assert result.get_advantage_in_pawns() == 1.5


def test_analyze_position_best_move():
    score = chess.engine.PovScore(chess.engine.Cp(30), chess.WHITE)
    with patch("chess.engine.SimpleEngine.popen_uci",
               return_value=make_engine_with_score(score, "d2d4")):
        service = AnalysisService("fake_path")
        result = service.analyze_position(START_FEN)
    assert result.best_move == "d2d4"


def test_analyze_position_mate():
    score = chess.engine.PovScore(chess.engine.Mate(3), chess.WHITE)
    with patch("chess.engine.SimpleEngine.popen_uci",
               return_value=make_engine_with_score(score, "d1h5")):
        service = AnalysisService("fake_path")
        result = service.analyze_position(START_FEN)
    assert result.is_mate is True
    assert result.mate_in_moves == 3


def test_analyze_position_negative_means_black_better():
    score = chess.engine.PovScore(chess.engine.Cp(-200), chess.WHITE)
    with patch("chess.engine.SimpleEngine.popen_uci",
               return_value=make_engine_with_score(score)):
        service = AnalysisService("fake_path")
        result = service.analyze_position(START_FEN)
    assert result.centipawns == -200
    assert result.get_advantage_in_pawns() == -2.0


def test_analyze_position_invalid_fen():
    service = AnalysisService("fake_path")
    with pytest.raises(HTTPException) as exc:
        service.analyze_position("this is not a fen")
    assert exc.value.status_code == 400


def test_analyze_position_engine_missing():
    with patch("chess.engine.SimpleEngine.popen_uci",
               side_effect=FileNotFoundError):
        service = AnalysisService("nonexistent_path")
        with pytest.raises(HTTPException) as exc:
            service.analyze_position(START_FEN)
    assert exc.value.status_code == 503


def test_analyze_game_multiple_positions():
    score = chess.engine.PovScore(chess.engine.Cp(20), chess.WHITE)
    fens = [START_FEN, START_FEN, START_FEN]
    with patch("chess.engine.SimpleEngine.popen_uci",
               return_value=make_engine_with_score(score)):
        service = AnalysisService("fake_path")
        results = service.analyze_game(fens)
    assert len(results) == 3
    assert all(isinstance(r, EvaluationResult) for r in results)


def test_analyze_game_invalid_fen_in_list():
    score = chess.engine.PovScore(chess.engine.Cp(20), chess.WHITE)
    with patch("chess.engine.SimpleEngine.popen_uci",
               return_value=make_engine_with_score(score)):
        service = AnalysisService("fake_path")
        with pytest.raises(HTTPException) as exc:
            service.analyze_game([START_FEN, "garbage"])
    assert exc.value.status_code == 400


def test_depth_is_configurable():
    service = AnalysisService("fake_path", depth=20)
    assert service.depth == 20