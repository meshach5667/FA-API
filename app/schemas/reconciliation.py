from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class ReconciliationStatusEnum(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"

class ReconciliationLineItemStatusEnum(str, Enum):
    matched = "matched"
    unmatched = "unmatched"
    disputed = "disputed"
    resolved = "resolved"

class ReconciliationBase(BaseModel):
    period_start: date
    period_end: date
    expected_total: Optional[float] = 0.0
    actual_total: Optional[float] = None
    notes: Optional[str] = None

class ReconciliationCreate(ReconciliationBase):
    pass

class ReconciliationUpdate(BaseModel):
    actual_total: Optional[float] = None
    variance: Optional[float] = None
    status: Optional[ReconciliationStatusEnum] = None
    notes: Optional[str] = None
    reconciled_by: Optional[int] = None

class ReconciliationLineItemBase(BaseModel):
    expected_amount: float
    actual_amount: Optional[float] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class ReconciliationLineItemOut(ReconciliationLineItemBase):
    id: int
    reconciliation_id: int
    payment_id: Optional[int] = None
    variance: Optional[float] = None
    status: ReconciliationLineItemStatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ReconciliationOut(ReconciliationBase):
    id: int
    business_id: int
    variance: Optional[float] = None
    status: ReconciliationStatusEnum
    created_at: datetime
    updated_at: datetime
    reconciled_by: Optional[int] = None
    reconciled_at: Optional[datetime] = None
    line_items: Optional[List[ReconciliationLineItemOut]] = []

    model_config = ConfigDict(from_attributes=True)

class ReconciliationSummary(BaseModel):
    total_reconciliations: int
    completed_reconciliations: int
    pending_reconciliations: int
    total_expected_amount: float
    total_actual_amount: float
    variance: float
    period_days: int
