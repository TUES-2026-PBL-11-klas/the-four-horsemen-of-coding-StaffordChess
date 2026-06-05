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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_verification_repo(db: AsyncSession = Depends(get_db)) -> EmailVerificationRepository:
    return EmailVerificationRepository(db)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
    verification_repo: EmailVerificationRepository = Depends(get_verification_repo),
) -> AuthService:
    return AuthService(user_repo, verification_repo)


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