from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date, time
from enum import Enum

class GroupStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"
    archived = "archived"

class GroupMemberRoleEnum(str, Enum):
    member = "member"
    moderator = "moderator"
    admin = "admin"

class GroupMemberStatusEnum(str, Enum):
    active = "active"
    pending = "pending"
    banned = "banned"

class PostTypeEnum(str, Enum):
    text = "text"
    image = "image"
    video = "video"
    link = "link"

# Group schemas
class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_private: bool = False
    max_members: Optional[int] = None

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_private: Optional[bool] = None
    max_members: Optional[int] = None
    status: Optional[GroupStatusEnum] = None

class GroupOut(GroupBase):
    id: int
    business_id: int
    status: GroupStatusEnum
    member_count: int = 0
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Group Member schemas
class GroupMemberOut(BaseModel):
    id: int
    group_id: int
    user_id: int
    role: GroupMemberRoleEnum
    status: GroupMemberStatusEnum
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)

class GroupJoinRequest(BaseModel):
    message: Optional[str] = None

# Group Post schemas
class GroupPostBase(BaseModel):
    content: str
    post_type: PostTypeEnum = PostTypeEnum.text
    media_url: Optional[str] = None

class GroupPostCreate(GroupPostBase):
    pass

class GroupPostOut(GroupPostBase):
    id: int
    group_id: int
    user_id: int
    likes_count: int = 0
    comments_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Group Event schemas
class GroupEventBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: date
    event_time: Optional[time] = None
    location: Optional[str] = None
    max_attendees: Optional[int] = None

class GroupEventCreate(GroupEventBase):
    pass

class GroupEventOut(GroupEventBase):
    id: int
    group_id: int
    created_by: int
    attendee_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Group Post Like schemas
class GroupPostLikeOut(BaseModel):
    id: int
    post_id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class GroupPostLikeToggleResponse(BaseModel):
    message: str
    liked: bool
    like_id: Optional[int] = None

# Group Post Comment schemas
class GroupPostCommentBase(BaseModel):
    content: str

class GroupPostCommentCreate(GroupPostCommentBase):
    pass

class GroupPostCommentOut(GroupPostCommentBase):
    id: int
    post_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
