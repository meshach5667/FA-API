from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum
from app.db.database import Base
from datetime import datetime
import enum

class AdminRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"

class AdminStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String)
    role = Column(Enum(AdminRole), default=AdminRole.ADMIN)
    status = Column(Enum(AdminStatus), default=AdminStatus.PENDING)
    is_active = Column(Boolean, default=True)
    approved_by = Column(Integer, nullable=True)  # ID of super admin who approved
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_initials(self):
        """Generate initials from full name"""
        if not self.full_name:
            return "AD"
        parts = self.full_name.strip().split()
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()
    
    def is_super_admin(self):
        return self.role == AdminRole.SUPER_ADMIN
    
    def is_approved(self):
        return self.status == AdminStatus.APPROVED
