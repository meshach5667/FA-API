from pydantic import BaseModel, ConfigDict, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime
from app.schemas.user import UserProfile  # or a minimal UserOut schema

class BookingBase(BaseModel):
    member_id: int
    date: datetime
    time_slot: str
    activity: Optional[str] = None
    notes: Optional[str] = None

class BookingCreate(BaseModel):
    center_id: int
    date: str  # ISO date string
    time_slot: str
    preferences: Optional[Dict] = None
    notes: Optional[str] = None

class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: int
    user: UserProfile  # <-- Add this
    center_id: int
    date: str
    time: str = Field(..., alias="time_slot")  # Maps time_slot to time
    preferences: Optional[Dict] = None
    notes: Optional[str] = None
    status: str
    rejection_reason: Optional[str]