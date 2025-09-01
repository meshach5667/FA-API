from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    username: str
    full_name: str
    email: str
    password: str

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class UserUpdate(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None

class ForgetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str

class CenterCheckInSummary(BaseModel):
    center_id: int
    center_name: str
    total_minutes: int

class UserProfile(BaseModel):
    username: str
    email: str
    full_name: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    balance: float
    plan: str
    flex_credit: int
    checkin_summary: List[CenterCheckInSummary]
    achievements: Dict[str, Any]
    created_year: int
    created_month: int