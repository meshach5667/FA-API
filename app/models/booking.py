from sqlalchemy import Column, Integer, String, Date, Time, JSON, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from app.db.database import Base
from enum import Enum as PyEnum
from datetime import datetime

class BookingStatus(str, PyEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"
    completed = "completed"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, nullable=False)  # Changed from user_id to match API
    center_id = Column(Integer, nullable=True)
    business_id = Column(Integer, nullable=False)
    activity_id = Column(Integer, nullable=True)
    schedule_id = Column(Integer, nullable=True)
    date = Column(DateTime, nullable=False)
    time_slot = Column(String, nullable=False)
    activity = Column(String, nullable=True)  # Added for activity name
    preferences = Column(JSON, nullable=True)
    notes = Column(String, nullable=True)
    status = Column(Enum(BookingStatus), default=BookingStatus.pending)
    rejection_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # user = relationship("User")  # Commented out to avoid startup errors
    # center = relationship("Center")  # Commented out to avoid startup errors
    # business = relationship("Business", back_populates="bookings")  # Commented out to avoid startup errors
    # activity = relationship("Activity", back_populates="bookings")  # Commented out to avoid startup errors
    # schedule = relationship("Schedule", back_populates="bookings")  # Commented out to avoid startup errors