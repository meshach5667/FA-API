from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class CenterCreate(BaseModel):
    name: str
    address: str
    state: str
    latitude: float
    longitude: float
    services: List[str]
    description: str
    booking_schedule: str
    cac_number: str
    bank_name: str
    account_number: str
    account_name: str
    credit_required: int  # Flex credit required for entry

class CenterOut(BaseModel):
    id: int
    name: str
    address: str
    state: str
    latitude: float
    longitude: float
    images: List[str]
    services: List[str]
    description: str
    booking_schedule: str
    credit_required: int  # Flex credit required for entry
    rating: Optional[float] = None
    comments: Optional[List[str]] = []

class CenterRating(BaseModel):
    rating: float

class CenterComment(BaseModel):
    comment: str