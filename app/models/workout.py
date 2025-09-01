from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Workout(Base):
    __tablename__ = "workouts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String, nullable=False)  # e.g., "cardio", "strength"
    start_time = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer, default=0)
    with_friends = Column(Boolean, default=False)

    # user = relationship("User")  # Commented out to avoid startup errors