from pydantic import BaseModel, ConfigDict, EmailStr, constr
from typing import Optional, List, Dict, Any
from datetime import datetime

class BusinessCreate(BaseModel):
    business_name: str
    email: EmailStr
    phone: str
    address: str
    password: str
    confirm_password: str

class BusinessLogin(BaseModel):
    email: EmailStr
    password: str

class BusinessBase(BaseModel):
    business_name: str
    email: EmailStr
    phone: str
    address: str

class BusinessOut(BusinessBase):
    id: int
    created_at: datetime
    balance: Optional[float] = 0.0

    model_config = ConfigDict(from_attributes=True)

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

class MembershipPlan(BaseModel):
    name: str
    price: float

class BusinessHour(BaseModel):
    open: str  # "06:00"
    close: str # "22:00"

class BusinessProfileBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str]
    address: Optional[str]
    state: Optional[str]
    country: Optional[str]
    logo_url: Optional[str]
    pictures: Optional[List[str]] = []  # Up to 5 picture URLs
    cac_number: Optional[str]
    membership_plans: Optional[List[MembershipPlan]]
    business_hours: Optional[Dict[str, BusinessHour]]
    description: Optional[str]
    longitude: Optional[float] = None   
    latitude: Optional[float] = None    

class BusinessProfileCreate(BusinessProfileBase):
    pass

class BusinessProfileUpdate(BusinessProfileBase):
    pass

class BusinessProfileOut(BusinessProfileBase):
    id: int
    business_id: int

    model_config = ConfigDict(from_attributes=True)

class BusinessProfileSummary(BaseModel):
    id: int
    business_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    logo_url: Optional[str] = None
    cac_number: Optional[str] = None
    membership_plans: Optional[List[MembershipPlan]] = None
    business_hours: Optional[Dict[str, BusinessHour]] = None
    description: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    achievements: Optional[Dict[str, Any]] = None
    created_year: Optional[int] = None
    created_month: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
