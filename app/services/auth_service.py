import secrets
from datetime import datetime, timedelta, timezone

from email_validator import validate_email, EmailNotValidError
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.repositories.user_repository import UserRepository
from app.repositories.email_verification_repository import EmailVerificationRepository
from app.schemas.auth_dto import UserCreate, UserLogin, VerifyEmail
from app.services.mail_service import send_verification_email
from app.utils.security import hash_password, verify_password, create_token


class AuthService:

    def __init__(self, user_repo: UserRepository, verification_repo: EmailVerificationRepository):
        self.user_repo = user_repo
        self.verification_repo = verification_repo

    def _generate_token(self) -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    def _is_expired(self, created_at: datetime) -> bool:
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - created_at
        return age > timedelta(minutes=settings.VERIFICATION_EXPIRE_MINUTES)

    async def register(self, data: UserCreate):
        try:
            validate_email(data.email, check_deliverability=True)
        except EmailNotValidError:
            raise HTTPException(status_code=400, detail="Email address is not valid")

        existing = await self.user_repo.get_by_email_or_username(data.email, data.username)
        if existing:
            raise HTTPException(status_code=409, detail="Username or email already registered")

        token = self._generate_token()
        try:
            user = await self.user_repo.create(
                username=data.username,
                email=data.email,
                hashed_password=hash_password(data.password),
            )
            await self.verification_repo.save_token(user.id, token)
            await send_verification_email(user.email, token)
            await self.user_repo.db.commit()
        except IntegrityError:
            await self.user_repo.db.rollback()
            raise HTTPException(status_code=409, detail="Username or email already registered")
        except Exception:
            await self.user_repo.db.rollback()
            raise HTTPException(status_code=400, detail="Could not send verification email")

        return {"message": "Registration successful. Check your email for the verification code."}

    async def resend_verification(self, email: str):
        generic = {"message": "If this email exists and is unverified, a new code has been sent."}

        user = await self.user_repo.get_by_email(email)
        if not user or user.is_active:
            return generic

        token = self._generate_token()
        try:
            await self.verification_repo.save_token(user.id, token)
            await send_verification_email(user.email, token)
            await self.user_repo.db.commit()
        except Exception:
            await self.user_repo.db.rollback()
            raise HTTPException(status_code=400, detail="Could not send verification email")

        return generic

    async def verify_email(self, data: VerifyEmail):
        user = await self.user_repo.get_by_email(data.email)
        if not user or user.is_active:
            raise HTTPException(status_code=400, detail="Invalid or expired verification code")

        verification = await self.verification_repo.get_by_user_id(user.id)
        if not verification or verification.is_verified:
            raise HTTPException(status_code=400, detail="Invalid or expired verification code")

        if self._is_expired(verification.created_at):
            raise HTTPException(status_code=400, detail="Invalid or expired verification code")

        if data.token != verification.token:
            raise HTTPException(status_code=400, detail="Invalid or expired verification code")

        await self.user_repo.activate(user)
        await self.verification_repo.mark_verified(verification)
        return {"message": "Email verified successfully. You can now log in."}

    async def login(self, data: UserLogin):
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Please verify your email before logging in")

        token = create_token(user.id, user.username)
        return {"access_token": token, "token_type": "bearer", "username": user.username}

    async def cleanup_unverified_users(self) -> int:
        threshold = datetime.now(timezone.utc) - timedelta(days=settings.UNVERIFIED_USER_EXPIRE_DAYS)
        return await self.user_repo.delete_unverified_older_than(threshold)