from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class CheckIn(Base):
    __tablename__ = "check_ins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    center_id = Column(Integer, ForeignKey("centers.id"), nullable=False)
    check_in_time = Column(DateTime, default=datetime.utcnow)
    timestamp = Column(DateTime, default=datetime.utcnow)  # Keep for compatibility
    status = Column(String, default="active")  # active, completed

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    member = relationship("Member", foreign_keys=[member_id])
    # center = relationship("Center")  # Commented out to avoid startup errors