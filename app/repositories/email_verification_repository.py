from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.email_verification import EmailVerification


class EmailVerificationRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> EmailVerification | None:
        result = await self.db.execute(
            select(EmailVerification).where(EmailVerification.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def save_token(self, user_id: int, token: str) -> EmailVerification:
        verification = await self.get_by_user_id(user_id)
        if verification is None:
            verification = EmailVerification(user_id=user_id, token=token)
            self.db.add(verification)
        else:
            verification.token = token
            verification.is_verified = False
            verification.created_at = datetime.now(timezone.utc)
        await self.db.flush()
        return verification

    async def mark_verified(self, verification: EmailVerification) -> None:
        verification.is_verified = True
        await self.db.commit()