from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func

from app.database import Base


class ChessGame(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    white_player_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    black_player_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    winner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    moves_pgn = Column(String, nullable=True)
    status = Column(String, default="ongoing")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    time_control = Column(String, nullable=False)
    result = Column(String, nullable=True)