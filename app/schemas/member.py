from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
from datetime import date, datetime

class MemberCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    date_of_birth: date
    membership_type: str
    emergency_contact_name: str
    emergency_contact_phone: str
    emergency_contact_relationship: str

class MemberUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    date_of_birth: Optional[date]
    membership_type: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relationship: Optional[str]
    is_active: Optional[bool]
    payment_status: Optional[str]  # "paid", "unpaid", "overdue"
    membership_status: Optional[str]  # "active", "inactive", "suspended", "expired"

class MemberOut(MemberCreate):
    id: int
    business_id: int
    is_active: bool = True
    payment_status: str = "unpaid"
    membership_status: str = "active"
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class MemberPaymentCreate(BaseModel):
    amount: float

class MemberPaymentOut(BaseModel):
    id: int
    member_id: int
    amount: float
    paid_at: datetime
    receipt_url: Optional[str] = None
    # Frontend compatibility fields
    date: datetime
    method: str = "Cash"  # Default payment method
    status: str = "paid"  # All recorded payments are considered paid

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_computed(cls, payment):
        return cls(
            id=payment.id,
            member_id=payment.member_id,
            amount=payment.amount,
            paid_at=payment.paid_at,
            receipt_url=payment.receipt_url,
            date=payment.paid_at,  # Map paid_at to date
            method="Cash",  # Default method
            status="paid"  # All payments are paid
        )

class MemberInvoiceCreate(BaseModel):
    amount: float
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class MemberInvoiceOut(BaseModel):
    id: int
    member_id: int
    amount: float
    description: Optional[str]
    issued_at: datetime
    due_date: Optional[datetime]
    is_paid: bool
    paid_at: Optional[datetime]
    receipt_url: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class MemberInvoiceUpdateStatus(BaseModel):
    is_paid: bool
    paid_at: Optional[datetime] = None
    receipt_url: Optional[str] = None