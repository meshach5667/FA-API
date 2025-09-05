from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import relationship  # Add this import
from datetime import datetime
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    name = Column(String)  # Add name field
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    country = Column(String, nullable=True)
    state = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)  # Add phone_number field
    balance = Column(Float, default=0.0)
    plan = Column(String, default="Free")
    flex_credit = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    bio = Column(String, nullable=True)
    avatar = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)  # Add profile_picture field
    is_active = Column(Boolean, default=True)  # Add is_active field
    
    # Add the notifications relationship here - temporarily commented out to fix startup
    # notifications = relationship("Notification", back_populates="user")
    # payments = relationship("Payment", back_populates="user")
    
    def get_initials(self):
        """Generate initials from name or full_name"""
        name_to_use = self.name or self.full_name
        if not name_to_use:
            return "US"  # Default for User
        parts = name_to_use.strip().split()
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()