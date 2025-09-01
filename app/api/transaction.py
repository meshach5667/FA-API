from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional
from datetime import datetime, date, timedelta
from app.db.database import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionCreate, TransactionOut, TransactionUpdate,
    TransactionSummary, TransactionReport
)
from app.api.deps import get_current_business

router = APIRouter()

@router.post("/", response_model=TransactionOut)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Create a new transaction record"""
    transaction = Transaction(
        business_id=current_business.id,
        **transaction_data.dict()
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

@router.get("/", response_model=List[TransactionOut])
def get_transactions(
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    transaction_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(50, le=200)
):
    """Get transactions for the current business with optional filters"""
    query = db.query(Transaction).filter(Transaction.business_id == current_business.id)
    
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if status:
        query = query.filter(Transaction.status == status)
    if date_from:
        query = query.filter(func.date(Transaction.created_at) >= date_from)
    if date_to:
        query = query.filter(func.date(Transaction.created_at) <= date_to)
    
    return query.order_by(desc(Transaction.created_at)).limit(limit).all()

@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get a specific transaction by ID"""
    transaction = db.query(Transaction).filter(
        and_(
            Transaction.id == transaction_id,
            Transaction.business_id == current_business.id
        )
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction

@router.put("/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Update a transaction record"""
    transaction = db.query(Transaction).filter(
        and_(
            Transaction.id == transaction_id,
            Transaction.business_id == current_business.id
        )
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    for field, value in transaction_update.dict(exclude_unset=True).items():
        setattr(transaction, field, value)
    
    db.commit()
    db.refresh(transaction)
    return transaction

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Delete a transaction record"""
    transaction = db.query(Transaction).filter(
        and_(
            Transaction.id == transaction_id,
            Transaction.business_id == current_business.id
        )
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}

@router.post("/{transaction_id}/refund")
def refund_transaction(
    transaction_id: int,
    refund_amount: Optional[float] = Query(None, description="Partial refund amount"),
    reason: Optional[str] = Query(None, description="Refund reason"),
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Process a refund for a transaction"""
    transaction = db.query(Transaction).filter(
        and_(
            Transaction.id == transaction_id,
            Transaction.business_id == current_business.id
        )
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction.status != "completed":
        raise HTTPException(status_code=400, detail="Can only refund completed transactions")
    
    # Determine refund amount
    if refund_amount is None:
        refund_amount = transaction.amount
    elif refund_amount > transaction.amount:
        raise HTTPException(status_code=400, detail="Refund amount cannot exceed transaction amount")
    
    # Create refund transaction
    refund_transaction = Transaction(
        business_id=current_business.id,
        transaction_type="refund",
        amount=-refund_amount,  # Negative amount for refund
        currency=transaction.currency,
        status="completed",
        reference=f"REFUND-{transaction.reference}",
        description=f"Refund for transaction {transaction.reference}. Reason: {reason or 'No reason provided'}",
        payment_id=transaction.payment_id,
        related_transaction_id=transaction_id
    )
    
    db.add(refund_transaction)
    
    # Update original transaction status if full refund
    if refund_amount == transaction.amount:
        transaction.status = "refunded"
    
    db.commit()
    db.refresh(refund_transaction)
    
    return {
        "message": "Refund processed successfully",
        "refund_transaction_id": refund_transaction.id,
        "refund_amount": refund_amount
    }

@router.get("/summary/stats", response_model=TransactionSummary)
def get_transaction_summary(
    days: int = Query(30, description="Number of days for summary"),
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get transaction summary statistics"""
    start_date = datetime.now().date() - timedelta(days=days)
    
    transactions = db.query(Transaction).filter(
        and_(
            Transaction.business_id == current_business.id,
            func.date(Transaction.created_at) >= start_date
        )
    ).all()
    
    total_transactions = len(transactions)
    completed_transactions = sum(1 for t in transactions if t.status == "completed")
    pending_transactions = sum(1 for t in transactions if t.status == "pending")
    failed_transactions = sum(1 for t in transactions if t.status == "failed")
    refunded_transactions = sum(1 for t in transactions if t.status == "refunded")
    
    total_amount = sum(t.amount for t in transactions if t.status == "completed")
    refund_amount = sum(abs(t.amount) for t in transactions if t.transaction_type == "refund")
    net_amount = total_amount - refund_amount
    
    # Transaction types breakdown
    payment_transactions = sum(1 for t in transactions if t.transaction_type == "payment")
    refund_transactions = sum(1 for t in transactions if t.transaction_type == "refund")
    fee_transactions = sum(1 for t in transactions if t.transaction_type == "fee")
    other_transactions = total_transactions - payment_transactions - refund_transactions - fee_transactions
    
    return TransactionSummary(
        total_transactions=total_transactions,
        completed_transactions=completed_transactions,
        pending_transactions=pending_transactions,
        failed_transactions=failed_transactions,
        refunded_transactions=refunded_transactions,
        total_amount=total_amount,
        refund_amount=refund_amount,
        net_amount=net_amount,
        payment_transactions=payment_transactions,
        refund_transactions=refund_transactions,
        fee_transactions=fee_transactions,
        other_transactions=other_transactions,
        period_days=days
    )

@router.get("/reports/daily", response_model=List[TransactionReport])
def get_daily_transaction_report(
    date_from: date = Query(..., description="Start date for report"),
    date_to: date = Query(..., description="End date for report"),
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get daily transaction report"""
    # Query transactions grouped by date
    results = db.query(
        func.date(Transaction.created_at).label('date'),
        func.count(Transaction.id).label('total_transactions'),
        func.sum(Transaction.amount).label('total_amount'),
        func.count(func.distinct(Transaction.payment_id)).label('unique_payments')
    ).filter(
        and_(
            Transaction.business_id == current_business.id,
            func.date(Transaction.created_at) >= date_from,
            func.date(Transaction.created_at) <= date_to,
            Transaction.status == "completed"
        )
    ).group_by(func.date(Transaction.created_at)).all()
    
    return [
        TransactionReport(
            date=result.date,
            total_transactions=result.total_transactions or 0,
            total_amount=result.total_amount or 0.0,
            unique_payments=result.unique_payments or 0
        )
        for result in results
    ]

@router.get("/balance/current")
def get_current_balance(
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get current balance based on all completed transactions"""
    total_balance = db.query(func.sum(Transaction.amount)).filter(
        and_(
            Transaction.business_id == current_business.id,
            Transaction.status == "completed"
        )
    ).scalar() or 0.0
    
    return {
        "current_balance": total_balance,
        "currency": "USD",
        "last_updated": datetime.now()
    }
