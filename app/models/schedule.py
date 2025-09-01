from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum
from datetime import datetime
from enum import Enum
from app.db.database import Base

class ScheduleStatus(str, Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class RecurrenceType(str, Enum):
    none = "none"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    capacity = Column(Integer, nullable=False, default=10)
    current_bookings = Column(Integer, nullable=False, default=0)
    instructor = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    price = Column(Float, nullable=True, default=0.0)
    status = Column(SQLEnum(ScheduleStatus), nullable=False, default=ScheduleStatus.scheduled)
    is_recurring = Column(Boolean, nullable=False, default=False)
    recurrence_type = Column(SQLEnum(RecurrenceType), nullable=True, default=RecurrenceType.none)
    recurrence_end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # business = relationship("Business", back_populates="schedules")  # Commented out to avoid startup errors
    # activity = relationship("Activity")  # Commented out to avoid startup errors
    # bookings = relationship("Booking", back_populates="schedule")  # Commented out to avoid startup errors
