from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
 
from app.models.rating_history import RatingHistory
 
 
class RatingHistoryRepository:
 
    def __init__(self, db: AsyncSession):
        self.db = db
 
    async def add_snapshot(self, user_id: int, rating_value: int) -> RatingHistory:
        snapshot = RatingHistory(user_id=user_id, rating=rating_value)
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot
 
    async def get_user_history(self, user_id: int) -> list[RatingHistory]:
        result = await self.db.execute(
            select(RatingHistory)
            .where(RatingHistory.user_id == user_id)
            .order_by(RatingHistory.date)
        )
        return list(result.scalars().all())
 