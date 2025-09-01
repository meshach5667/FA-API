from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    is_active = Column(Boolean, default=True)
    points_reward = Column(Integer, default=0)

    # Relationships
    # business = relationship("Business", back_populates="challenges")  # Commented out to avoid startup errors

class MonthlyChallenge(Base):
    __tablename__ = "monthly_challenges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    points_goal = Column(Integer, default=0)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    is_active = Column(Boolean, default=True)

    # Relationships
    # business = relationship("Business", back_populates="monthly_challenges")  # Commented out to avoid startup errors