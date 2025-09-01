from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum
from datetime import datetime
from enum import Enum
from app.db.database import Base

class ReconciliationStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"

class ReconciliationLineItemStatus(str, Enum):
    matched = "matched"
    unmatched = "unmatched"
    disputed = "disputed"
    resolved = "resolved"

class Reconciliation(Base):
    __tablename__ = "reconciliations"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    expected_total = Column(Float, nullable=False, default=0.0)
    actual_total = Column(Float, nullable=True)
    variance = Column(Float, nullable=True)
    status = Column(SQLEnum(ReconciliationStatus), nullable=False, default=ReconciliationStatus.pending)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reconciled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reconciled_at = Column(DateTime, nullable=True)
    
    # Relationships
    # business = relationship("Business", back_populates="reconciliations")  # Commented out to avoid startup errors
    line_items = relationship("ReconciliationLineItem", back_populates="reconciliation", cascade="all, delete-orphan")

class ReconciliationLineItem(Base):
    __tablename__ = "reconciliation_line_items"
    
    id = Column(Integer, primary_key=True, index=True)
    reconciliation_id = Column(Integer, ForeignKey("reconciliations.id"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    expected_amount = Column(Float, nullable=False)
    actual_amount = Column(Float, nullable=True)
    variance = Column(Float, nullable=True)
    status = Column(SQLEnum(ReconciliationLineItemStatus), nullable=False, default=ReconciliationLineItemStatus.unmatched)
    description = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reconciliation = relationship("Reconciliation", back_populates="line_items")
    payment = relationship("Payment")
