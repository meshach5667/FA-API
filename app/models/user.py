from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship  # Add this import
from datetime import datetime
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    country = Column(String, nullable=True)
    state = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    balance = Column(Float, default=0.0)
    plan = Column(String, default="Free")
    flex_credit = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    bio = Column(String, nullable=True)
    avatar = Column(String, nullable=True)
    
    # Add the notifications relationship here - temporarily commented out to fix startup
    # notifications = relationship("Notification", back_populates="user")
    # payments = relationship("Payment", back_populates="user")