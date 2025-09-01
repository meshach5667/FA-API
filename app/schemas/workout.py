from pydantic import BaseModel, ConfigDict
from datetime import datetime

class WorkoutOut(BaseModel):
    id: int
    user_id: int
    type: str
    start_time: datetime
    duration_minutes: int
    with_friends: bool

    model_config = ConfigDict(from_attributes=True)
