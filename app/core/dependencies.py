from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.email_verification_repository import EmailVerificationRepository
from app.services.auth_service import AuthService
from app.utils.security import decode_token
from app.repositories.chess_game_repository import ChessGameRepository
from app.repositories.rating_history_repository import RatingHistoryRepository
from app.services.profile_service import ProfileService
from app.services.lobby_service import LobbyService
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
_lobby_service = LobbyService()

def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_verification_repo(db: AsyncSession = Depends(get_db)) -> EmailVerificationRepository:
    return EmailVerificationRepository(db)

def get_game_repo(db: AsyncSession = Depends(get_db)) -> ChessGameRepository:
    return ChessGameRepository(db)


def get_rating_repo(db: AsyncSession = Depends(get_db)) -> RatingHistoryRepository:
    return RatingHistoryRepository(db)

def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
    verification_repo: EmailVerificationRepository = Depends(get_verification_repo),
) -> AuthService:
    return AuthService(user_repo, verification_repo)

def get_profile_service(
    user_repo: UserRepository = Depends(get_user_repo),
    game_repo: ChessGameRepository = Depends(get_game_repo),
    rating_repo: RatingHistoryRepository = Depends(get_rating_repo),
) -> ProfileService:
    return ProfileService(user_repo, game_repo, rating_repo)

def get_lobby_service() -> LobbyService:
    return _lobby_service

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user