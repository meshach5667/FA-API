from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, time, date
from enum import Enum

class ScheduleStatusEnum(str, Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class RecurrenceTypeEnum(str, Enum):
    none = "none"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"

class ScheduleBase(BaseModel):
    activity_id: int
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    capacity: int = 10
    instructor: Optional[str] = None
    location: Optional[str] = None
    price: Optional[float] = 0.0
    is_recurring: bool = False
    recurrence_type: Optional[RecurrenceTypeEnum] = None
    recurrence_end_date: Optional[date] = None

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    capacity: Optional[int] = None
    instructor: Optional[str] = None
    location: Optional[str] = None
    price: Optional[float] = None
    status: Optional[ScheduleStatusEnum] = None
    is_recurring: Optional[bool] = None
    recurrence_type: Optional[RecurrenceTypeEnum] = None
    recurrence_end_date: Optional[date] = None

class ScheduleOut(ScheduleBase):
    id: int
    business_id: int
    status: ScheduleStatusEnum
    current_bookings: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ScheduleSearch(BaseModel):
    search_date: Optional[date] = None
    time_from: Optional[time] = None
    time_to: Optional[time] = None
    activity_id: Optional[int] = None
    instructor: Optional[str] = None
    available_only: bool = True

class ScheduleAvailability(BaseModel):
    schedule_id: int
    total_capacity: int
    current_bookings: int
    available_spots: int
    is_available: bool
    start_time: datetime
    end_time: datetime
