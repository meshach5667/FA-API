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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    membership_type: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    is_active: Optional[bool] = None
    payment_status: Optional[str] = None  # "paid", "unpaid", "overdue"
    membership_status: Optional[str] = None  # "active", "inactive", "suspended", "expired"

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
    payment_method: Optional[str] = "card"

class MemberPaymentOut(BaseModel):
    id: int
    member_id: int
    amount: float
    paid_at: datetime
    payment_method: Optional[str] = "card"
    receipt_url: Optional[str] = None
    # Frontend compatibility fields
    date: datetime
    method: str = "card"  # Default payment method
    status: str = "paid"  # All recorded payments are considered paid
    # Member info for display
    member: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_computed(cls, payment):
        member_info = None
        if hasattr(payment, 'member') and payment.member:
            member_info = {
                "id": payment.member.id,
                "first_name": payment.member.first_name,
                "last_name": payment.member.last_name,
                "full_name": f"{payment.member.first_name} {payment.member.last_name}"
            }
        
        return cls(
            id=payment.id,
            member_id=payment.member_id,
            amount=payment.amount,
            paid_at=payment.paid_at,
            payment_method=getattr(payment, 'payment_method', 'card'),
            receipt_url=payment.receipt_url,
            date=payment.paid_at,  # Map paid_at to date
            method=getattr(payment, 'payment_method', 'card'),  # Use actual payment method
            status="paid",  # All payments are paid
            member=member_info
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