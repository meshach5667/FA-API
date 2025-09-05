from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class CheckIn(Base):
    __tablename__ = "check_ins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    member_id = Column(Integer, nullable=True)  # Remove foreign key constraint for now
    center_id = Column(Integer, nullable=True)  # Remove foreign key constraint for now
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True)  # Add business_id
    check_in_time = Column(DateTime, default=datetime.utcnow)
    timestamp = Column(DateTime, default=datetime.utcnow)  # Keep for compatibility
    tokens_used = Column(Integer, default=0)  # Add tokens_used field
    status = Column(String, default="active")  # active, completed

    # Relationships - commented out to avoid startup errors
    # user = relationship("User", foreign_keys=[user_id])
    # business = relationship("Business")