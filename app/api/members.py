from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.db.database import get_db
from app.models.member import Member, MemberPayment, MemberInvoice
from app.schemas.member import (
    MemberCreate, MemberUpdate, MemberOut, MemberPaymentCreate, MemberPaymentOut,
    MemberInvoiceCreate, MemberInvoiceOut, MemberInvoiceUpdateStatus
)
from app.api.deps import get_current_business
from datetime import datetime, timedelta
from typing import List

router = APIRouter()

@router.post("/", response_model=MemberOut)
def create_member(
    member: MemberCreate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    db_member = Member(**member.dict(), business_id=current_business.id)
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

@router.get("/", response_model=List[MemberOut])
def list_members(
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    return db.query(Member).filter(Member.business_id == current_business.id).all()

@router.get("/{member_id}", response_model=MemberOut)
def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    member = db.query(Member).filter(Member.id == member_id, Member.business_id == current_business.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

# Note: Test endpoint removed for security - use authenticated endpoint in production

@router.put("/{member_id}", response_model=MemberOut)
def update_member(
    member_id: int,
    member_update: MemberUpdate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    member = db.query(Member).filter(Member.id == member_id, Member.business_id == current_business.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Get the update data, excluding unset fields
    update_data = member_update.dict(exclude_unset=True)
    print(f"Updating member {member_id} with data: {update_data}")
    
    try:
        # Validate specific fields that might cause issues
        if "payment_status" in update_data:
            valid_payment_statuses = ["paid", "unpaid", "overdue"]
            if update_data["payment_status"] not in valid_payment_statuses:
                raise HTTPException(
                    status_code=422, 
                    detail=f"Invalid payment_status. Must be one of: {valid_payment_statuses}"
                )
        
        if "membership_status" in update_data:
            valid_membership_statuses = ["active", "inactive", "suspended", "expired"]
            if update_data["membership_status"] not in valid_membership_statuses:
                raise HTTPException(
                    status_code=422, 
                    detail=f"Invalid membership_status. Must be one of: {valid_membership_statuses}"
                )
        
        # Apply the updates
        for key, value in update_data.items():
            if hasattr(member, key):  # Only update fields that exist on the model
                setattr(member, key, value)
            else:
                print(f"Warning: Field {key} not found on Member model")
        
        # Update the updated_at timestamp
        member.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(member)
        return member
        
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating member: {str(e)}")
        raise HTTPException(
            status_code=422, 
            detail=f"Failed to update member: {str(e)}"
        )

@router.patch("/{member_id}/payment-status")
def update_member_payment_status(
    member_id: int,
    payment_data: dict,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Update member payment status and automatically handle membership status"""
    member = db.query(Member).filter(Member.id == member_id, Member.business_id == current_business.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    payment_status = payment_data.get("payment_status")
    if payment_status not in ["paid", "unpaid", "overdue"]:
        raise HTTPException(
            status_code=422, 
            detail="Invalid payment_status. Must be one of: paid, unpaid, overdue"
        )
    
    try:
        # Update payment status
        member.payment_status = payment_status
        
        # Automatically update membership status based on payment status
        if payment_status == "paid":
            member.is_active = True
            member.membership_status = "active"
        elif payment_status in ["unpaid", "overdue"]:
            member.is_active = False
            member.membership_status = "inactive"
        
        member.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(member)
        
        return {
            "message": f"Payment status updated to {payment_status}",
            "member": {
                "id": member.id,
                "payment_status": member.payment_status,
                "membership_status": member.membership_status,
                "is_active": member.is_active
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=422, 
            detail=f"Failed to update payment status: {str(e)}"
        )

# Note: Test endpoint removed for security - use authenticated endpoint in production
        print(f"Database error updating member {member_id}: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"Could not update member: {str(e)}"
        )

@router.delete("/{member_id}")
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    member = db.query(Member).filter(Member.id == member_id, Member.business_id == current_business.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"detail": "Member deleted"}

# Payments
@router.get("/payments/all", response_model=List[MemberPaymentOut])
def list_all_payments(
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get all member payments for the current business"""
    payments = db.query(MemberPayment).join(Member).filter(
        Member.business_id == current_business.id
    ).order_by(MemberPayment.paid_at.desc()).all()
    
    return [MemberPaymentOut.from_orm_with_computed(payment) for payment in payments]

@router.get("/payments/summary")
def get_payments_summary(
    days: int = Query(30, description="Number of days for summary"),
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get payment summary statistics"""
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get payments in the period
    payments = db.query(MemberPayment).join(Member).filter(
        and_(
            Member.business_id == current_business.id,
            MemberPayment.paid_at >= start_date,
            MemberPayment.paid_at <= end_date
        )
    ).all()
    
    total_revenue = sum(p.amount for p in payments)
    total_payments = len(payments)
    average_payment = total_revenue / total_payments if total_payments > 0 else 0
    
    # This month vs last month
    now = datetime.now()
    this_month_start = datetime(now.year, now.month, 1)
    last_month_start = datetime(now.year, now.month - 1, 1) if now.month > 1 else datetime(now.year - 1, 12, 1)
    last_month_end = this_month_start - timedelta(days=1)
    
    this_month_payments = db.query(func.sum(MemberPayment.amount)).join(Member).filter(
        and_(
            Member.business_id == current_business.id,
            MemberPayment.paid_at >= this_month_start
        )
    ).scalar() or 0
    
    last_month_payments = db.query(func.sum(MemberPayment.amount)).join(Member).filter(
        and_(
            Member.business_id == current_business.id,
            MemberPayment.paid_at >= last_month_start,
            MemberPayment.paid_at <= last_month_end
        )
    ).scalar() or 0
    
    growth_percentage = 0
    if last_month_payments > 0:
        growth_percentage = ((this_month_payments - last_month_payments) / last_month_payments) * 100
    
    return {
        "total_payments": total_payments,
        "total_revenue": float(total_revenue),
        "average_payment": float(average_payment),
        "this_month_revenue": float(this_month_payments),
        "last_month_revenue": float(last_month_payments),
        "growth_percentage": float(growth_percentage)
    }

@router.post("/{member_id}/payments", response_model=MemberPaymentOut)
def add_payment(
    member_id: int,
    payment: MemberPaymentCreate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    member = db.query(Member).filter(Member.id == member_id, Member.business_id == current_business.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Create the payment
    db_payment = MemberPayment(
        member_id=member.id, 
        amount=payment.amount,
        payment_method=payment.payment_method or "card"
    )
    db.add(db_payment)
    
    # Update member status when payment is made
    member.payment_status = "paid"
    member.membership_status = "active"
    member.is_active = True  # Ensure member is marked as active
    
    db.commit()
    db.refresh(db_payment)
    # TODO: Generate receipt and send via WhatsApp or email here
    return MemberPaymentOut.from_orm_with_computed(db_payment)

@router.get("/{member_id}/payments", response_model=List[MemberPaymentOut])
def list_payments(
    member_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    member = db.query(Member).filter(Member.id == member_id, Member.business_id == current_business.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    payments = db.query(MemberPayment).filter(MemberPayment.member_id == member.id).all()
    # Return payments with computed fields for frontend compatibility
    return [MemberPaymentOut.from_orm_with_computed(payment) for payment in payments]

# Invoices
@router.post("/{member_id}/invoices", response_model=MemberInvoiceOut)
def create_invoice(
    member_id: int,
    invoice: MemberInvoiceCreate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    member = db.query(Member).filter(Member.id == member_id, Member.business_id == current_business.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db_invoice = MemberInvoice(member_id=member.id, **invoice.dict())
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    # TODO: Send invoice via email/WhatsApp here if needed
    return db_invoice

@router.get("/{member_id}/invoices", response_model=List[MemberInvoiceOut])
def list_invoices(
    member_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    member = db.query(Member).filter(Member.id == member_id, Member.business_id == current_business.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return db.query(MemberInvoice).filter(MemberInvoice.member_id == member.id).all()

@router.patch("/invoices/{invoice_id}/status", response_model=MemberInvoiceOut)
def update_invoice_status(
    invoice_id: int,
    status: MemberInvoiceUpdateStatus,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    invoice = db.query(MemberInvoice).join(Member).filter(
        MemberInvoice.id == invoice_id,
        Member.business_id == current_business.id
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice.is_paid = status.is_paid
    invoice.paid_at = status.paid_at or (datetime.utcnow() if status.is_paid else None)
    invoice.receipt_url = status.receipt_url
    
    # If invoice is marked as paid, update member status
    if status.is_paid:
        member = db.query(Member).filter(Member.id == invoice.member_id).first()
        if member:
            member.payment_status = "paid"
            member.membership_status = "active"
    
    db.commit()
    db.refresh(invoice)
    return invoice

# Update member membership status
@router.patch("/{member_id}/membership-status")
def update_member_membership_status(
    member_id: int,
    membership_data: dict,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Update member membership status"""
    member = db.query(Member).filter(
        Member.id == member_id, 
        Member.business_id == current_business.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    membership_status = membership_data.get("membership_status")
    if membership_status not in ["active", "inactive", "suspended", "expired"]:
        raise HTTPException(status_code=422, detail="Invalid membership status")
    
    try:
        member.membership_status = membership_status
        # Update is_active based on membership status
        member.is_active = membership_status == "active"
        member.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(member)
        
        return {
            "message": f"Membership status updated to {membership_status}", 
            "member": {
                "id": member.id,
                "membership_status": member.membership_status,
                "is_active": member.is_active
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=422, 
            detail=f"Failed to update membership status: {str(e)}"
        )

# Get member statistics
@router.get("/stats/overview")
def get_member_statistics(
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    total_members = db.query(func.count(Member.id)).filter(
        Member.business_id == current_business.id
    ).scalar() or 0
    
    active_members = db.query(func.count(Member.id)).filter(
        Member.business_id == current_business.id,
        Member.is_active == True
    ).scalar() or 0
    
    inactive_members = total_members - active_members
    
    # Payment status breakdown
    paid_members = db.query(func.count(Member.id)).filter(
        Member.business_id == current_business.id,
        Member.payment_status == "paid"
    ).scalar() or 0
    
    unpaid_members = db.query(func.count(Member.id)).filter(
        Member.business_id == current_business.id,
        Member.payment_status == "unpaid"
    ).scalar() or 0
    
    overdue_members = db.query(func.count(Member.id)).filter(
        Member.business_id == current_business.id,
        Member.payment_status == "overdue"
    ).scalar() or 0
    
    # Membership status breakdown
    active_memberships = db.query(func.count(Member.id)).filter(
        Member.business_id == current_business.id,
        Member.membership_status == "active"
    ).scalar() or 0
    
    suspended_memberships = db.query(func.count(Member.id)).filter(
        Member.business_id == current_business.id,
        Member.membership_status == "suspended"
    ).scalar() or 0
    
    expired_memberships = db.query(func.count(Member.id)).filter(
        Member.business_id == current_business.id,
        Member.membership_status == "expired"
    ).scalar() or 0
    
    # Members created in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_members = db.query(func.count(Member.id)).filter(
        Member.business_id == current_business.id,
        Member.created_at >= thirty_days_ago
    ).scalar() or 0
    
    # Payment statistics (from invoices)
    total_invoices = db.query(func.count(MemberInvoice.id)).join(Member).filter(
        Member.business_id == current_business.id
    ).scalar() or 0
    
    paid_invoices = db.query(func.count(MemberInvoice.id)).join(Member).filter(
        Member.business_id == current_business.id,
        MemberInvoice.is_paid == True
    ).scalar() or 0
    
    pending_payments = total_invoices - paid_invoices
    
    total_revenue = db.query(func.sum(MemberInvoice.amount)).join(Member).filter(
        Member.business_id == current_business.id,
        MemberInvoice.is_paid == True
    ).scalar() or 0.0
    
    return {
        "total_members": total_members,
        "active_members": active_members,
        "inactive_members": inactive_members,
        "new_members": new_members,
        "payment_status": {
            "paid": paid_members,
            "unpaid": unpaid_members,
            "overdue": overdue_members
        },
        "membership_status": {
            "active": active_memberships,
            "suspended": suspended_memberships,
            "expired": expired_memberships
        },
        "financial": {
            "total_invoices": total_invoices,
            "paid_invoices": paid_invoices,
            "pending_payments": pending_payments,
            "total_revenue": float(total_revenue),
            "payment_rate": (paid_invoices / total_invoices * 100) if total_invoices > 0 else 0
        }
    }