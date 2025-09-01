from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from app.db.database import get_db
from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.models.business import Business
from app.api.deps import get_current_business

router = APIRouter()

# Pydantic schemas
class BookingBase(BaseModel):
    member_id: int
    business_id: int
    date: datetime
    time_slot: str
    activity: Optional[str] = None
    notes: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class BookingOut(BookingBase):
    id: int
    status: BookingStatus
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class BookingUpdate(BaseModel):
    status: Optional[BookingStatus] = None
    rejection_reason: Optional[str] = None

class BusinessReport(BaseModel):
    total_bookings: int
    total_bookings_last_month: int
    total_bookings_change: int
    approval_rate: float
    approval_rate_last_month: float
    approval_rate_change: float
    most_popular_time: Optional[str]
    monthly_trends: List[dict]
    popular_activities: List[dict]

# Helper function to verify business access
def verify_business_access(db: Session, business_id: int, current_business: Business):
    if current_business.id != business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this business"
        )
    return current_business

# Booking endpoints
@router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    """Create a new booking for a business"""
    # Example: get business_id from user's membership, or related center, etc.
    # business_id = ... (derive from context)
    # For now, you can require it as a query param or similar if needed

    new_booking = Booking(
        **booking.dict(),
        business_id=booking.business_id,  # set here
        status=BookingStatus.pending
    )
    
    # Verify business access
    verify_business_access(db, booking.business_id, current_business)
    
    # Check for existing booking at same time
    existing = db.query(Booking).filter(
        Booking.business_id == booking.business_id,
        Booking.date == booking.date,
        Booking.time_slot == booking.time_slot
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking already exists for this time slot"
        )

    try:
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)
        return new_booking
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating booking: {str(e)}"
        )

@router.get("/business/{business_id}/bookings", response_model=List[BookingOut])
def get_business_bookings(
    business_id: int,
    status: Optional[BookingStatus] = None,
    date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    """Get all bookings for a specific business with optional filters"""
    verify_business_access(db, business_id, current_business)
    
    query = db.query(Booking).filter(Booking.business_id == business_id)
    
    if status:
        query = query.filter(Booking.status == status)
    if date:
        query = query.filter(Booking.date == date)
    
    return query.order_by(Booking.date, Booking.time_slot).all()

@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    """Get a specific booking by ID"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    verify_business_access(db, booking.business_id, current_business)
    return booking

@router.put("/{booking_id}", response_model=BookingOut)
def update_booking(
    booking_id: int,
    booking_update: BookingUpdate,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    """Update a booking's status or other details"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    verify_business_access(db, booking.business_id, current_business)
    
    for field, value in booking_update.dict(exclude_unset=True).items():
        setattr(booking, field, value)
    
    try:
        db.commit()
        db.refresh(booking)
        return booking
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating booking: {str(e)}"
        )

@router.post("/{booking_id}/approve", response_model=BookingOut)
def approve_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    """Approve a pending booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    verify_business_access(db, booking.business_id, current_business)
    
    if booking.status != BookingStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending bookings can be approved"
        )
    
    booking.status = BookingStatus.approved
    booking.rejection_reason = None
    
    try:
        db.commit()
        db.refresh(booking)
        return booking
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving booking: {str(e)}"
        )

@router.post("/{booking_id}/reject", response_model=BookingOut)
def reject_booking(
    booking_id: int,
    reason: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    """Reject a pending booking with a reason"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    verify_business_access(db, booking.business_id, current_business)
    
    if booking.status != BookingStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending bookings can be rejected"
        )
    
    booking.status = BookingStatus.rejected
    booking.rejection_reason = reason
    
    try:
        db.commit()
        db.refresh(booking)
        return booking
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rejecting booking: {str(e)}"
        )

@router.get("/business/{business_id}/report", response_model=BusinessReport)
def get_business_report(
    business_id: int,
    months: int = 6,  # Default to 6 months of trend data
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    """Generate a business report with booking analytics"""
    verify_business_access(db, business_id, current_business)
    
    now = datetime.utcnow()
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first_of_last_month = (first_of_this_month - timedelta(days=1)).replace(day=1)
    last_of_last_month = first_of_this_month - timedelta(days=1)

    # Total bookings calculations
    total_bookings = db.query(Booking).filter(
        Booking.business_id == business_id,
        Booking.date >= first_of_this_month,
        Booking.date <= now
    ).count()

    total_bookings_last_month = db.query(Booking).filter(
        Booking.business_id == business_id,
        Booking.date >= first_of_last_month,
        Booking.date <= last_of_last_month
    ).count()

    # Approval rate calculations
    def calculate_approval_rate(start_date, end_date):
        total = db.query(Booking).filter(
            Booking.business_id == business_id,
            Booking.date >= start_date,
            Booking.date <= end_date
        ).count()
        
        approved = db.query(Booking).filter(
            Booking.business_id == business_id,
            Booking.date >= start_date,
            Booking.date <= end_date,
            Booking.status == BookingStatus.approved
        ).count()
        
        return (approved / total * 100) if total else 0

    approval_rate = calculate_approval_rate(first_of_this_month, now)
    approval_rate_last_month = calculate_approval_rate(first_of_last_month, last_of_last_month)

    # Most popular time slot
    popular_time = db.query(
        Booking.time_slot, func.count(Booking.id).label("count")
    ).filter(
        Booking.business_id == business_id
    ).group_by(Booking.time_slot).order_by(func.count(Booking.id).desc()).first()

    # Monthly trends
    trends = db.query(
        extract('year', Booking.date).label('year'),
        extract('month', Booking.date).label('month'),
        func.count(Booking.id).label('count')
    ).filter(
        Booking.business_id == business_id,
        Booking.date >= (now - timedelta(days=30*months))  # months parameter
    ).group_by('year', 'month').order_by('year', 'month').all()

    # Popular activities
    popular_activities = []
    if hasattr(Booking, "activity"):
        activities = db.query(
            Booking.activity, func.count(Booking.id).label("count")
        ).filter(
            Booking.business_id == business_id
        ).group_by(Booking.activity).order_by(func.count(Booking.id).desc()).limit(5).all()
        popular_activities = [{"activity": a, "count": c} for a, c in activities]

    return {
        "total_bookings": total_bookings,
        "total_bookings_last_month": total_bookings_last_month,
        "total_bookings_change": total_bookings - total_bookings_last_month,
        "approval_rate": approval_rate,
        "approval_rate_last_month": approval_rate_last_month,
        "approval_rate_change": approval_rate - approval_rate_last_month,
        "most_popular_time": popular_time[0] if popular_time else None,
        "monthly_trends": [
            {"year": int(year), "month": int(month), "count": count}
            for year, month, count in trends
        ],
        "popular_activities": popular_activities,
    }