from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.db.database import Base
from datetime import datetime

class SuperAdmin(Base):
    __tablename__ = "super_admins"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    # Add more fields as needed

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_super_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)