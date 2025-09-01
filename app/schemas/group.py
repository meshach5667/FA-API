from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    business_id: int

class GroupCreate(GroupBase):
    pass

class GroupOut(GroupBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool = True
    created_at: datetime

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
