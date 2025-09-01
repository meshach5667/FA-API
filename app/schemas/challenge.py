from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class MonthlyChallengeOut(BaseModel):
    id: int
    user_id: int
    name: str
    completed: bool
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
