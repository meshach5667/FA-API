from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from enum import Enum

class TransactionTypeEnum(str, Enum):
    payment = "payment"
    refund = "refund"
    fee = "fee"
    payout = "payout"
    adjustment = "adjustment"

class TransactionStatusEnum(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

class TransactionBase(BaseModel):
    transaction_type: TransactionTypeEnum
    amount: float
    currency: str = "USD"
    description: Optional[str] = None
    reference: Optional[str] = None
    payment_id: Optional[int] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatusEnum] = None
    description: Optional[str] = None
    reference: Optional[str] = None

class TransactionOut(TransactionBase):
    id: int
    business_id: int
    status: TransactionStatusEnum
    balance_after: Optional[float] = None
    related_transaction_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TransactionSummary(BaseModel):
    total_transactions: int
    completed_transactions: int
    pending_transactions: int
    failed_transactions: int
    refunded_transactions: int
    total_amount: float
    refund_amount: float
    net_amount: float
    payment_transactions: int
    refund_transactions: int
    fee_transactions: int
    other_transactions: int
    period_days: int

class TransactionReport(BaseModel):
    date: date
    total_transactions: int
    total_amount: float
    unique_payments: int
