from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Date, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    event_category = Column(String(100), nullable=True)
    event_properties = Column(JSON, nullable=True)
    session_id = Column(String(200), nullable=True)
    device_type = Column(String(50), nullable=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    event_timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    # business = relationship("Business", back_populates="analytics_events")  # Commented out to avoid startup errors
    # user = relationship("User")  # Commented out to avoid startup errors

class BusinessMetrics(Base):
    __tablename__ = "business_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    date = Column(Date, nullable=False)
    total_revenue = Column(Float, nullable=False, default=0.0)
    total_bookings = Column(Integer, nullable=False, default=0)
    unique_users = Column(Integer, nullable=False, default=0)
    avg_session_duration = Column(Float, nullable=False, default=0.0)
    total_check_ins = Column(Integer, nullable=False, default=0)
    total_events = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # business = relationship("Business", back_populates="business_metrics")  # Commented out to avoid startup errors
