from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base
import enum

class AdStatusEnum(str, enum.Enum):
    active = "active"
    scheduled = "scheduled"
    ended = "ended"
    draft = "draft"

class AdTargetTypeEnum(str, enum.Enum):
    all = "all"
    location = "location"
    user_group = "user_group"

class Advertisement(Base):
    __tablename__ = "advertisements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(Enum(AdStatusEnum), default=AdStatusEnum.draft)
    
    # Target configuration stored as JSON
    target_type = Column(Enum(AdTargetTypeEnum), default=AdTargetTypeEnum.all)
    target_locations = Column(JSON, nullable=True)  # List of location names
    target_user_groups = Column(JSON, nullable=True)  # List of user group IDs
    
    # Analytics
    clicks = Column(Integer, default=0)
    views = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)  # Admin ID who created this ad
    
    # Optional: Track user interactions
    # user_interactions = relationship("AdInteraction", back_populates="advertisement")
