from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class CommunityBase(BaseModel):
    name: str
    description: Optional[str] = None
    business_id: int
    max_members: Optional[int] = None

class CommunityOut(CommunityBase):
    id: int
    member_count: int
    created_at: datetime
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)

class CommunityCreate(BaseModel):
    name: str
    description: Optional[str]
    category: str
    image: Optional[str]

class CommunityMessageCreate(BaseModel):
    community_id: int
    message: str
    image: Optional[str] = None

class CommunityMessageOut(BaseModel):
    id: int
    community_id: int
    center_id: int
    message: str
    image: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class CommunityCommentCreate(BaseModel):
    message_id: int
    comment: str

class CommunityCommentOut(BaseModel):
    id: int
    message_id: int
    user_id: int
    comment: str

    model_config = ConfigDict(from_attributes=True)

class CommunityJoinOut(BaseModel):
    joined: bool
    members: int