from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime
from app.models.admin import AdminRole, AdminStatus

class AdminBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    username: Optional[str] = None

class AdminCreate(AdminBase):
    password: str
    role: Optional[AdminRole] = AdminRole.ADMIN

class AdminUpdate(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    role: Optional[AdminRole] = None
    status: Optional[AdminStatus] = None
    is_active: Optional[bool] = None

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class AdminOut(AdminBase):
    id: int
    role: AdminRole
    status: AdminStatus
    is_active: bool = True
    initials: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AdminApproval(BaseModel):
    admin_id: int
    action: str  # "approve", "reject", "suspend"
    notes: Optional[str] = None
