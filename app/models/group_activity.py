from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Date, Time, Text
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum
from datetime import datetime
from enum import Enum
from app.db.database import Base

class GroupStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    archived = "archived"

class GroupMemberRole(str, Enum):
    member = "member"
    moderator = "moderator"
    admin = "admin"

class GroupMemberStatus(str, Enum):
    active = "active"
    pending = "pending"
    banned = "banned"

class PostType(str, Enum):
    text = "text"
    image = "image"
    video = "video"
    link = "link"

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, nullable=False)  # Remove foreign key constraint temporarily
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    is_private = Column(Boolean, nullable=False, default=False)
    max_members = Column(Integer, nullable=True)
    member_count = Column(Integer, nullable=False, default=0)
    status = Column(SQLEnum(GroupStatus), nullable=False, default=GroupStatus.active)
    created_by = Column(Integer, nullable=True)  # Remove foreign key constraint temporarily
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - temporarily commented out to fix startup issues
    # business = relationship("Business", back_populates="groups")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    posts = relationship("GroupPost", back_populates="group", cascade="all, delete-orphan")
    events = relationship("GroupEvent", back_populates="group", cascade="all, delete-orphan")

class GroupMember(Base):
    __tablename__ = "group_members"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(SQLEnum(GroupMemberRole), nullable=False, default=GroupMemberRole.member)
    status = Column(SQLEnum(GroupMemberStatus), nullable=False, default=GroupMemberStatus.active)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    group = relationship("Group", back_populates="members")
    # # user = relationship("User")  # Commented out to avoid import issues

class GroupPost(Base):
    __tablename__ = "group_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    post_type = Column(SQLEnum(PostType), nullable=False, default=PostType.text)
    media_url = Column(String(500), nullable=True)
    likes_count = Column(Integer, nullable=False, default=0)
    comments_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    group = relationship("Group", back_populates="posts")
    likes = relationship("GroupPostLike", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("GroupPostComment", back_populates="post", cascade="all, delete-orphan")
    # # user = relationship("User")  # Commented out to avoid import issues

class GroupEvent(Base):
    __tablename__ = "group_events"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    event_date = Column(Date, nullable=False)
    event_time = Column(Time, nullable=True)
    location = Column(String(200), nullable=True)
    max_attendees = Column(Integer, nullable=True)
    attendee_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    group = relationship("Group", back_populates="events")
    # # creator = relationship("User")  # Commented out to avoid import issues

# Keep the original GroupActivity class for backwards compatibility
class GroupActivity(Base):
    __tablename__ = "group_activities"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # participant
    host_id = Column(Integer, ForeignKey("users.id"))  # host/creator
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True)  # linked activity
    name = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    # user = relationship("User", foreign_keys=[user_id])
    # host = relationship("User", foreign_keys=[host_id])
    # activity = relationship("Activity", back_populates="group_activities")  # Commented out to avoid import issues


class GroupPostLike(Base):
    __tablename__ = "group_post_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("group_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("GroupPost", back_populates="likes")
    # user = relationship("User")  # Commented out to avoid import issues

class GroupPostComment(Base):
    __tablename__ = "group_post_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("group_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    post = relationship("GroupPost", back_populates="comments")
    # user = relationship("User")  # Commented out to avoid import issues

