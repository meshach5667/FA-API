from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class NotificationCreate(BaseModel):
    user_id: int
    type: str
    title: str
    message: str
    is_read: Optional[bool] = False

class NotificationOut(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
