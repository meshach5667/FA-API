from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional, List

class SuperAdminOut(BaseModel):
    id: int
    email: str
    model_config = ConfigDict(from_attributes=True)

class AdminMetrics(BaseModel):
    total_users: int
    total_businesses: int
    total_checkins: int
    total_revenue: float
    active_users_last_30_days: int

class SystemHealth(BaseModel):
    database_status: str
    api_status: str
    last_check: datetime
    errors: List[str] = []

class AdminCreate(BaseModel):
    email: EmailStr
    password: str
    is_super_admin: bool = False

class AdminOut(BaseModel):
    id: int
    email: EmailStr
    is_super_admin: bool
    created_at: datetime
    last_login: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class AdminLogin(BaseModel):
    email: EmailStr
    password: str