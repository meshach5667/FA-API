from pydantic import BaseModel, ConfigDict, ConfigDict
from typing import Optional

class RewardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: str
    points_required: int
    category: str
    reward_type: str
    reward_value: float
    reward_description: str

class UserRewardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    reward: RewardOut
    claimed: int
    progress: int
    total: int

class UserPointsOut(BaseModel):
    available_points: int
    total_points: int
    
