from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class Member(Base):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    membership_type = Column(String, nullable=False)
    emergency_contact_name = Column(String, nullable=False)
    emergency_contact_phone = Column(String, nullable=False)
    emergency_contact_relationship = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    payment_status = Column(String, default="unpaid")  # "paid", "unpaid", "overdue"
    membership_status = Column(String, default="active")  # "active", "inactive", "suspended", "expired"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payments = relationship("MemberPayment", back_populates="member")

class MemberPayment(Base):
    __tablename__ = "member_payments"
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    amount = Column(Float, nullable=False)
    paid_at = Column(DateTime, default=datetime.utcnow)
    payment_method = Column(String, default="card")  # "card", "cash", "transfer", etc.
    receipt_url = Column(String, nullable=True)  # Optional: link to PDF/image receipt

    member = relationship("Member", back_populates="payments")

class MemberInvoice(Base):
    __tablename__ = "member_invoices"
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    issued_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    is_paid = Column(Boolean, default=False)
    paid_at = Column(DateTime, nullable=True)
    receipt_url = Column(String, nullable=True)  # Optional: link to PDF/image receipt

    member = relationship("Member", backref="invoices")