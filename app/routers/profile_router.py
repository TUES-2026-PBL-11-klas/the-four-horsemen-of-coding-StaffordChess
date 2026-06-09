from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_profile_service
from app.models.user import User
from app.schemas.profile_dto import ProfileResponse, GameHistoryItem, RatingPoint
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    return await service.fetch_profile_data(current_user.id)


@router.get("/me/games", response_model=list[GameHistoryItem])
async def get_game_history(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    return await service.fetch_game_history(current_user.id)


@router.get("/me/rating", response_model=list[RatingPoint])
async def get_rating_graph(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    return await service.generate_rating_chart_points(current_user.id)