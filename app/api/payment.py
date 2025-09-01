from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional
from datetime import datetime, date, timedelta
from app.db.database import get_db
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentOut, PaymentUpdate
from app.api.deps import get_current_business, get_current_user

router = APIRouter()

@router.post("/", response_model=PaymentOut)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Create a new payment record"""
    payment = Payment(
        business_id=current_business.id,
        **payment_data.dict()
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

@router.get("/", response_model=List[PaymentOut])
def get_payments(
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    status: Optional[str] = Query(None),
    payment_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(50, le=100)
):
    """Get payments for the current business with optional filters"""
    query = db.query(Payment).filter(Payment.business_id == current_business.id)
    
    if status:
        query = query.filter(Payment.status == status)
    if payment_type:
        query = query.filter(Payment.payment_type == payment_type)
    if date_from:
        query = query.filter(func.date(Payment.created_at) >= date_from)
    if date_to:
        query = query.filter(func.date(Payment.created_at) <= date_to)
    
    return query.order_by(desc(Payment.created_at)).limit(limit).all()

@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get a specific payment by ID"""
    payment = db.query(Payment).filter(
        and_(
            Payment.id == payment_id,
            Payment.business_id == current_business.id
        )
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return payment

@router.put("/{payment_id}", response_model=PaymentOut)
def update_payment(
    payment_id: int,
    payment_update: PaymentUpdate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Update a payment record"""
    payment = db.query(Payment).filter(
        and_(
            Payment.id == payment_id,
            Payment.business_id == current_business.id
        )
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    for field, value in payment_update.dict(exclude_unset=True).items():
        setattr(payment, field, value)
    
    db.commit()
    db.refresh(payment)
    return payment

@router.delete("/{payment_id}")
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Delete a payment record"""
    payment = db.query(Payment).filter(
        and_(
            Payment.id == payment_id,
            Payment.business_id == current_business.id
        )
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    db.delete(payment)
    db.commit()
    return {"message": "Payment deleted successfully"}

@router.get("/stats/summary")
def get_payment_summary(
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    days: int = Query(30, description="Number of days for summary")
):
    """Get payment summary statistics"""
    start_date = datetime.now().date() - timedelta(days=days)
    
    total_payments = db.query(func.count(Payment.id)).filter(
        and_(
            Payment.business_id == current_business.id,
            func.date(Payment.created_at) >= start_date,
            Payment.status == "completed"
        )
    ).scalar() or 0
    
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        and_(
            Payment.business_id == current_business.id,
            func.date(Payment.created_at) >= start_date,
            Payment.status == "completed"
        )
    ).scalar() or 0.0
    
    pending_payments = db.query(func.count(Payment.id)).filter(
        and_(
            Payment.business_id == current_business.id,
            Payment.status == "pending"
        )
    ).scalar() or 0
    
    failed_payments = db.query(func.count(Payment.id)).filter(
        and_(
            Payment.business_id == current_business.id,
            func.date(Payment.created_at) >= start_date,
            Payment.status == "failed"
        )
    ).scalar() or 0
    
    return {
        "total_payments": total_payments,
        "total_revenue": total_revenue,
        "pending_payments": pending_payments,
        "failed_payments": failed_payments,
        "period_days": days
    }

# Add user-specific endpoints after the business endpoints

@router.post("/user/create", response_model=PaymentOut)
def create_user_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new payment record for current user"""
    payment = Payment(
        user_id=current_user.id,
        **payment_data.dict(exclude={"user_id"})
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

@router.get("/user/history", response_model=List[PaymentOut])
def get_user_payments(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    status: Optional[str] = Query(None),
    payment_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(50, le=100)
):
    """Get payment history for the current user with optional filters"""
    query = db.query(Payment).filter(Payment.user_id == current_user.id)
    
    if status:
        query = query.filter(Payment.status == status)
    if payment_type:
        query = query.filter(Payment.payment_type == payment_type)
    if date_from:
        query = query.filter(func.date(Payment.created_at) >= date_from)
    if date_to:
        query = query.filter(func.date(Payment.created_at) <= date_to)
    
    return query.order_by(desc(Payment.created_at)).limit(limit).all()

@router.post("/user/topup")
def topup_flex_credits(
    amount: float,
    payment_method: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Top up user's flex credits"""
    from app.models.user import User
    
    # Calculate credits based on amount (example rate: 1 credit per $1)
    credits_to_add = int(amount)
    
    # Create payment record
    payment = Payment(
        user_id=current_user.id,
        amount=amount,
        payment_type="flex_credit",
        payment_method=payment_method,
        status="completed",  # In production, this would be pending until verified
        description=f"Flex credit top-up: {credits_to_add} credits"
    )
    
    # Update user's flex credit balance
    user = db.query(User).filter(User.id == current_user.id).first()
    user.flex_credit += credits_to_add
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    return {
        "message": "Top-up successful",
        "credits_added": credits_to_add,
        "new_balance": user.flex_credit,
        "payment": payment
    }

@router.post("/user/subscription")
def create_subscription(
    plan_type: str,
    amount: float,
    payment_method: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a subscription payment for user"""
    from app.models.user import User
    
    # Create payment record
    payment = Payment(
        user_id=current_user.id,
        amount=amount,
        payment_type="subscription",
        payment_method=payment_method,
        status="completed",  # In production, this would be pending until verified
        description=f"Subscription: {plan_type}"
    )
    
    # Update user's plan
    user = db.query(User).filter(User.id == current_user.id).first()
    user.plan = plan_type
    user.balance += amount  # Update balance
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    return {
        "message": "Subscription created successfully",
        "plan": plan_type,
        "amount": amount,
        "payment": payment
    }

@router.get("/user/balance")
def get_user_balance(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get user's current balance and flex credits"""
    return {
        "user_id": current_user.id,
        "balance": current_user.balance,
        "flex_credit": current_user.flex_credit,
        "plan": current_user.plan
    }
