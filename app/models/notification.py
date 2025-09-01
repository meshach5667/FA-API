from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.database import Base

class NotificationType(str, enum.Enum):
    SUBSCRIPTION = "subscription"
    NEARBY_GYM = "nearby_gym"
    GYM_VISIT = "gym_visit"
    REWARD = "reward"
    COMMUNITY = "community"
    BOOKING = "booking"
    ACTIVITY = "activity"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(String)
    type = Column(Enum(NotificationType))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    link = Column(String, nullable=True)
    
    # user = relationship("User", back_populates="notifications")  # Commented out to avoid startup errors