from pydantic import BaseModel


class AnalyzePositionRequest(BaseModel):
    fen: str


class AnalyzeGameRequest(BaseModel):
    fens: list[str]


class EvaluationResponse(BaseModel):
    centipawns: int
    is_mate: bool
    mate_in_moves: int
    best_move: str | None
    advantage_in_pawns: float