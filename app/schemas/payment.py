from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

class PaymentStatusEnum(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"
    approved = "approved"

class PaymentTypeEnum(str, Enum):
    subscription = "subscription"
    flex_credit = "flex_credit"
    activity_booking = "activity_booking"
    gym_access = "gym_access"

class PaymentBase(BaseModel):
    amount: float
    currency: str = "USD"
    payment_type: PaymentTypeEnum
    payment_method: Optional[str] = None
    description: Optional[str] = None
    payment_metadata: Optional[str] = None

class PaymentCreate(PaymentBase):
    user_id: int
    business_id: Optional[int] = None

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatusEnum] = None
    reference: Optional[str] = None
    transaction_id: Optional[str] = None

class PaymentOut(PaymentBase):
    id: int
    user_id: int
    business_id: Optional[int] = None
    status: PaymentStatusEnum
    transaction_id: Optional[str] = None
    reference: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
