from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum
from datetime import datetime
from enum import Enum
from app.db.database import Base

class TransactionType(str, Enum):
    payment = "payment"
    refund = "refund"
    fee = "fee"
    payout = "payout"
    adjustment = "adjustment"

class TransactionStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(SQLEnum(TransactionStatus), nullable=False, default=TransactionStatus.pending)
    reference = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    balance_after = Column(Float, nullable=True)
    related_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # business = relationship("Business", back_populates="transactions")  # Commented out to avoid startup errors
    payment = relationship("Payment")
    related_transaction = relationship("Transaction", remote_side=[id])
