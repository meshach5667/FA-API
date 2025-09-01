from pydantic import BaseModel, ConfigDict, validator
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum

class AdStatusEnum(str, Enum):
    active = "active"
    scheduled = "scheduled"
    ended = "ended"
    draft = "draft"

class AdTargetTypeEnum(str, Enum):
    all = "all"
    location = "location"
    user_group = "user_group"

class AdTarget(BaseModel):
    type: AdTargetTypeEnum
    locations: Optional[List[str]] = None
    user_groups: Optional[List[str]] = None

class AdvertisementBase(BaseModel):
    title: str
    description: str
    start_date: datetime
    end_date: datetime
    target_type: AdTargetTypeEnum = AdTargetTypeEnum.all
    target_locations: Optional[List[str]] = None
    target_user_groups: Optional[List[str]] = None

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class AdvertisementCreate(AdvertisementBase):
    image_url: str

class AdvertisementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[AdStatusEnum] = None
    target_type: Optional[AdTargetTypeEnum] = None
    target_locations: Optional[List[str]] = None
    target_user_groups: Optional[List[str]] = None

class AdvertisementOut(AdvertisementBase):
    id: int
    image_url: str
    status: AdStatusEnum
    clicks: int
    views: int
    created_at: datetime
    updated_at: datetime
    
    # Computed target field for frontend compatibility
    @property
    def target(self) -> AdTarget:
        return AdTarget(
            type=self.target_type,
            locations=self.target_locations,
            user_groups=self.target_user_groups
        )

    model_config = ConfigDict(from_attributes=True)

class AdvertisementStats(BaseModel):
    total_ads: int
    active_ads: int
    scheduled_ads: int
    ended_ads: int
    draft_ads: int
    total_views: int
    total_clicks: int
    ctr: float  # Click-through rate

class AdAnalytics(BaseModel):
    ad_id: int
    views_today: int
    clicks_today: int
    views_this_week: int
    clicks_this_week: int
    views_this_month: int
    clicks_this_month: int
    ctr_today: float
    ctr_this_week: float
    ctr_this_month: float
