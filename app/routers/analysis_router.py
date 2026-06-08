from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from app.core.dependencies import get_analysis_service, get_current_user
from app.models.user import User
from app.schemas.analysis_dto import (
    AnalyzePositionRequest,
    AnalyzeGameRequest,
    EvaluationResponse,
)
from app.services.analysis_service import AnalysisService
from app.domain.evaluation_result import EvaluationResult

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _to_response(result: EvaluationResult) -> EvaluationResponse:
    return EvaluationResponse(
        centipawns=result.centipawns,
        is_mate=result.is_mate,
        mate_in_moves=result.mate_in_moves,
        best_move=result.best_move,
        advantage_in_pawns=result.get_advantage_in_pawns(),
    )


@router.post("/position", response_model=EvaluationResponse)
async def analyze_position(
    data: AnalyzePositionRequest,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    result = await run_in_threadpool(service.analyze_position, data.fen)
    return _to_response(result)


@router.post("/game", response_model=list[EvaluationResponse])
async def analyze_game(
    data: AnalyzeGameRequest,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    results = await run_in_threadpool(service.analyze_game, data.fens)
    return [_to_response(r) for r in results]