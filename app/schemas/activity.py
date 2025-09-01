from pydantic import BaseModel, ConfigDict, field_serializer, ConfigDict
from typing import Optional, List
from datetime import datetime, date

class ActivityBase(BaseModel):
    name: str
    description: Optional[str] = None
    business_id: int
    duration: Optional[int] = None  # in minutes
    price: Optional[float] = None

class ActivityCreate(ActivityBase):
    center_id: int
    date: str  # ISO date string
    time: str  # "HH:MM"
    location: str
    activity_type: Optional[str] = None
    capacity: Optional[int] = None
    instructor: Optional[str] = None

class ActivityOut(ActivityBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    center_id: int = 1
    is_active: bool = True
    created_at: datetime
    join_count: int = 0
    date: date  # Keep as date type, will be serialized
    time: str
    location: str
    activity_type: Optional[str] = None
    capacity: Optional[int] = None
    instructor: Optional[str] = None

    @field_serializer('date')
    def serialize_date(self, date_value):
        if isinstance(date_value, date):
            return date_value.isoformat()
        return date_value

    @field_serializer('created_at')
    def serialize_datetime(self, datetime_value):
        if isinstance(datetime_value, datetime):
            return datetime_value.isoformat()
        return datetime_value

class ActivityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None  # ISO date string
    time: Optional[str] = None
    location: Optional[str] = None
    activity_type: Optional[str] = None
    capacity: Optional[int] = None
    duration: Optional[int] = None
    instructor: Optional[str] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None

class ActivityCommentCreate(BaseModel):
    activity_id: int
    comment: str

class ActivityCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    activity_id: int
    user_id: int
    comment: str