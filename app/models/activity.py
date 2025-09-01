from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, Text, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    center_id = Column(Integer, nullable=True, default=1)  # Remove foreign key constraint temporarily
    business_id = Column(Integer, nullable=False)  # Remove foreign key constraint temporarily
    name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(String, nullable=False)
    location = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    join_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    # Additional fields for frontend compatibility
    activity_type = Column(String, nullable=True)
    capacity = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)  # in minutes
    instructor = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships - commented out to avoid import issues
    # center = relationship("Center")
    # business = relationship("Business", back_populates="activities")
    # bookings = relationship("Booking", back_populates="activity")
    # group_activities = relationship("GroupActivity", back_populates="activity")