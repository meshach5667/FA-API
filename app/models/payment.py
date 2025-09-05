from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base
import enum

class PaymentStatusEnum(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"
    approved = "approved"

class PaymentTypeEnum(str, enum.Enum):
    subscription = "subscription"
    flex_credit = "flex_credit"
    activity_booking = "activity_booking"
    gym_access = "gym_access"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True)
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    payment_type = Column(Enum(PaymentTypeEnum), nullable=False)
    status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.pending)
    
    # Transaction details
    transaction_id = Column(String, unique=True, nullable=True)
    payment_method = Column(String, nullable=True)  # card, bank_transfer, etc.
    reference = Column(String, nullable=True)
    
    # Metadata
    description = Column(String, nullable=True)
    payment_metadata = Column(String, nullable=True)  # JSON string for additional data
    
    # Approval workflow
    approved_by = Column(Integer, nullable=True)  # Temporarily removed FK constraint
    approved_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - temporarily commented out to avoid startup errors
    # user = relationship("User", back_populates="payments")
    # business = relationship("Business", back_populates="payments")
    # approver = relationship("Admin", foreign_keys=[approved_by])
    
    # For compatibility with existing code
    @property
    def method(self):
        return self.payment_method
    
    @property
    def timestamp(self):
        return self.created_at