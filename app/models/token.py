from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.db.database import Base

class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True)
    
    # Token details
    token_type = Column(String, nullable=False)  # access, refresh, reset, etc.
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    admin = relationship("Admin", foreign_keys=[admin_id])
    business = relationship("Business", foreign_keys=[business_id])

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def create_token(cls, token_value: str, token_type: str, expires_in_minutes: int = 60, user_id=None, admin_id=None, business_id=None):
        """Create a new token"""
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        return cls(
            token=token_value,
            token_type=token_type,
            expires_at=expires_at,
            user_id=user_id,
            admin_id=admin_id,
            business_id=business_id
        )
