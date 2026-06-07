from fastapi import APIRouter, Depends

from app.core.dependencies import get_auth_service, get_current_user
from app.models.user import User
from app.schemas.auth_dto import (
    UserCreate,
    UserLogin,
    VerifyEmail,
    ResendVerification,
    TokenResponse,
    MessageResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse)
async def register(data: UserCreate, service: AuthService = Depends(get_auth_service)):
    return await service.register(data)


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(data: VerifyEmail, service: AuthService = Depends(get_auth_service)):
    return await service.verify_email(data)


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(data: ResendVerification, service: AuthService = Depends(get_auth_service)):
    return await service.resend_verification(data.email)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, service: AuthService = Depends(get_auth_service)):
    return await service.login(data)


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "current_rating": current_user.current_rating,
    }