from sqlalchemy import Column, Integer, DateTime, ForeignKey, func
 
from app.database import Base
 
 
class RatingHistory(Base):
    __tablename__ = "rating_history"
 
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now()) 