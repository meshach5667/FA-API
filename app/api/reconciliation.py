from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional
from datetime import datetime, date, timedelta
from app.db.database import get_db
from app.models.reconciliation import Reconciliation, ReconciliationLineItem
from app.models.payment import Payment
from app.schemas.reconciliation import (
    ReconciliationCreate, ReconciliationOut, ReconciliationUpdate,
    ReconciliationLineItemOut, ReconciliationSummary
)
from app.api.deps import get_current_business

router = APIRouter()

@router.post("/", response_model=ReconciliationOut)
def create_reconciliation(
    reconciliation_data: ReconciliationCreate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Create a new reconciliation record"""
    reconciliation = Reconciliation(
        business_id=current_business.id,
        **reconciliation_data.dict()
    )
    
    # Auto-populate with payments if not provided
    if not reconciliation_data.expected_total:
        start_date = reconciliation_data.period_start
        end_date = reconciliation_data.period_end
        
        payments = db.query(Payment).filter(
            and_(
                Payment.business_id == current_business.id,
                func.date(Payment.created_at) >= start_date,
                func.date(Payment.created_at) <= end_date,
                Payment.status == "completed"
            )
        ).all()
        
        reconciliation.expected_total = sum(p.amount for p in payments)
        
        # Create line items for each payment
        db.add(reconciliation)
        db.commit()
        db.refresh(reconciliation)
        
        for payment in payments:
            line_item = ReconciliationLineItem(
                reconciliation_id=reconciliation.id,
                payment_id=payment.id,
                expected_amount=payment.amount,
                actual_amount=payment.amount,
                status="matched"
            )
            db.add(line_item)
        
        db.commit()
    else:
        db.add(reconciliation)
        db.commit()
        db.refresh(reconciliation)
    
    return reconciliation

@router.get("/", response_model=List[ReconciliationOut])
def get_reconciliations(
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100)
):
    """Get reconciliation records for the current business"""
    query = db.query(Reconciliation).filter(
        Reconciliation.business_id == current_business.id
    )
    
    if status:
        query = query.filter(Reconciliation.status == status)
    
    return query.order_by(desc(Reconciliation.created_at)).limit(limit).all()

@router.get("/{reconciliation_id}", response_model=ReconciliationOut)
def get_reconciliation(
    reconciliation_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get a specific reconciliation by ID"""
    reconciliation = db.query(Reconciliation).filter(
        and_(
            Reconciliation.id == reconciliation_id,
            Reconciliation.business_id == current_business.id
        )
    ).first()
    
    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    
    return reconciliation

@router.put("/{reconciliation_id}", response_model=ReconciliationOut)
def update_reconciliation(
    reconciliation_id: int,
    reconciliation_update: ReconciliationUpdate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Update a reconciliation record"""
    reconciliation = db.query(Reconciliation).filter(
        and_(
            Reconciliation.id == reconciliation_id,
            Reconciliation.business_id == current_business.id
        )
    ).first()
    
    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    
    for field, value in reconciliation_update.dict(exclude_unset=True).items():
        setattr(reconciliation, field, value)
    
    db.commit()
    db.refresh(reconciliation)
    return reconciliation

@router.get("/{reconciliation_id}/line-items", response_model=List[ReconciliationLineItemOut])
def get_reconciliation_line_items(
    reconciliation_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get line items for a specific reconciliation"""
    reconciliation = db.query(Reconciliation).filter(
        and_(
            Reconciliation.id == reconciliation_id,
            Reconciliation.business_id == current_business.id
        )
    ).first()
    
    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    
    return reconciliation.line_items

@router.get("/summary/stats", response_model=ReconciliationSummary)
def get_reconciliation_summary(
    days: int = Query(30, description="Number of days for summary"),
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get reconciliation summary statistics"""
    start_date = datetime.now().date() - timedelta(days=days)
    
    reconciliations = db.query(Reconciliation).filter(
        and_(
            Reconciliation.business_id == current_business.id,
            func.date(Reconciliation.created_at) >= start_date
        )
    ).all()
    
    total_reconciliations = len(reconciliations)
    completed_reconciliations = sum(1 for r in reconciliations if r.status == "completed")
    pending_reconciliations = sum(1 for r in reconciliations if r.status == "pending")
    
    total_expected = sum(r.expected_total for r in reconciliations)
    total_actual = sum(r.actual_total or 0 for r in reconciliations)
    variance = total_actual - total_expected
    
    return ReconciliationSummary(
        total_reconciliations=total_reconciliations,
        completed_reconciliations=completed_reconciliations,
        pending_reconciliations=pending_reconciliations,
        total_expected_amount=total_expected,
        total_actual_amount=total_actual,
        variance=variance,
        period_days=days
    )
