from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True)
    business_name = Column(String(100), unique=True)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(200))
    phone = Column(String(20))
    address = Column(String(200))
    reset_token = Column(String(100), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    balance = Column(Float, default=0.0)  # Add this field
    
    # Relationships - temporarily commented out to fix startup issues
    # payments = relationship("Payment", back_populates="business")
    # challenges = relationship("Challenge", back_populates="business")
    # monthly_challenges = relationship("MonthlyChallenge", back_populates="business")
    # activities = relationship("Activity", back_populates="business")
    # bookings = relationship("Booking", back_populates="business")
    # reconciliations = relationship("Reconciliation", back_populates="business")
    # schedules = relationship("Schedule", back_populates="business")
    # transactions = relationship("Transaction", back_populates="business")
    # groups = relationship("Group", back_populates="business")
    # analytics_events = relationship("AnalyticsEvent", back_populates="business")
    # business_metrics = relationship("BusinessMetrics", back_populates="business")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class BusinessProfile(Base):
    __tablename__ = "business_profiles"
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), unique=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    pictures = Column(JSON, nullable=True)  # List of picture URLs
    cac_number = Column(String, nullable=True)
    membership_plans = Column(JSON, nullable=True)  # [{"name": "Daily Pass", "price": 10}, ...]
    business_hours = Column(JSON, nullable=True)    # {"Monday": {"open": "06:00", "close": "22:00"}, ...}
    description = Column(String, nullable=True)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)

    business = relationship("Business")
