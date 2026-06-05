from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
 
from app.database import Base
 
 
class EmailVerification(Base):
    __tablename__ = "email_verifications"
 
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    token = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
 