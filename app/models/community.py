from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class Community(Base):
    __tablename__ = "communities"
    id = Column(Integer, primary_key=True, index=True)
    center_id = Column(Integer, nullable=True)  # Removed FK constraint
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Add creator
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    image = Column(String, nullable=True)
    members = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # creator = relationship("User")  # Commented out to avoid startup errors

class CommunityMessage(Base):
    __tablename__ = "community_messages"
    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"))
    center_id = Column(Integer, nullable=True)  # Removed FK constraint
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Add user
    message = Column(Text, nullable=False)
    image = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CommunityLike(Base):
    __tablename__ = "community_likes"
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("community_messages.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

class CommunityComment(Base):
    __tablename__ = "community_comments"
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("community_messages.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class CommunityMember(Base):
    __tablename__ = "community_members"
    id = Column(Integer, primary_key=True)
    community_id = Column(Integer, ForeignKey("communities.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)