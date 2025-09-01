from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional

class AdminBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class AdminCreate(AdminBase):
    password: str

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class AdminOut(AdminBase):
    id: int
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)
