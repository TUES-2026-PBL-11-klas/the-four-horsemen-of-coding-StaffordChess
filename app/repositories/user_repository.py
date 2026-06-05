from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.user import User



class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_email_or_username(self, email: str, username: str) -> User | None:
        result = await self.db.execute(
            select(User).where((User.email == email) | (User.username == username))
        )
        return result.scalars().first()

    async def create(self, username: str, email: str, hashed_password: str) -> User:
        user = User(username=username, email=email, hashed_password=hashed_password)
        self.db.add(user)
        await self.db.flush()
        return user

    async def activate(self, user: User) -> None:
        user.is_active = True
        await self.db.commit()

    async def delete_unverified_older_than(self, threshold: datetime) -> int:
        result = await self.db.execute(
            delete(User).where(
                User.is_active == False,
                User.created_at < threshold,
            )
        )
        await self.db.commit()
        return result.rowcount or 0