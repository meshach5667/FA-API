from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import List, Optional
from datetime import datetime, date, timedelta
from collections import defaultdict
from app.db.database import get_db
from app.models.analytics import AnalyticsEvent, BusinessMetrics
from app.models.payment import Payment
from app.models.booking import Booking
from app.models.activity import Activity
from app.models.user import User
from app.models.member import Member, MemberInvoice
from app.schemas.analytics import (
    AnalyticsEventCreate, AnalyticsEventOut, BusinessMetricsOut,
    DashboardMetrics, RevenueAnalytics, UserAnalytics, 
    ActivityAnalytics, ConversionFunnel
)
from app.api.deps import get_current_business, get_current_user

router = APIRouter()

# Test endpoint without authentication
@router.get("/test")
def test_analytics_data(db: Session = Depends(get_db)):
    """Test endpoint to check analytics data without auth"""
    try:
        from app.models.member import MemberPayment
        
        # Get all payments and members for testing
        payments = db.query(MemberPayment).all()
        members = db.query(Member).all()
        
        total_revenue = sum(float(p.amount) for p in payments) if payments else 0
        total_transactions = len(payments)
        total_members = len(members)
        active_members = len([m for m in members if m.is_active])
        
        return {
            "total_revenue": total_revenue,
            "total_transactions": total_transactions,
            "total_members": total_members,
            "active_members": active_members,
            "payments": [
                {
                    "id": p.id,
                    "amount": float(p.amount),
                    "member_name": f"{p.member.first_name} {p.member.last_name}" if p.member else "Unknown",
                    "date": str(p.paid_at) if hasattr(p, 'paid_at') else str(p.payment_date)
                } for p in payments[:5]  # Show first 5 payments
            ]
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to get analytics data"}

# Event Tracking
@router.post("/events", response_model=AnalyticsEventOut)
def track_event(
    event_data: AnalyticsEventCreate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    current_user = Depends(get_current_user)
):
    """Track an analytics event"""
    event = AnalyticsEvent(
        business_id=current_business.id,
        user_id=current_user.id,
        **event_data.dict()
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.get("/events", response_model=List[AnalyticsEventOut])
def get_events(
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    event_type: Optional[str] = Query(None),
    event_category: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get analytics events with filters"""
    query = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.business_id == current_business.id
    )
    
    if event_type:
        query = query.filter(AnalyticsEvent.event_type == event_type)
    if event_category:
        query = query.filter(AnalyticsEvent.event_category == event_category)
    if date_from:
        query = query.filter(func.date(AnalyticsEvent.event_timestamp) >= date_from)
    if date_to:
        query = query.filter(func.date(AnalyticsEvent.event_timestamp) <= date_to)
    
    return query.order_by(desc(AnalyticsEvent.event_timestamp)).limit(limit).all()

# Dashboard Analytics
@router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard_metrics(
    period_days: int = Query(30, description="Number of days for current period"),
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get key metrics for the analytics dashboard using real transaction data"""
    from app.models.member import MemberPayment
    
    end_date = date.today()
    start_date = end_date - timedelta(days=period_days)
    
    # Current period metrics - Use Member Payments as transactions and revenue
    current_revenue = db.query(func.sum(MemberPayment.amount)).join(Member).filter(
        and_(
            Member.business_id == current_business.id,
            func.date(MemberPayment.paid_at) >= start_date,
            func.date(MemberPayment.paid_at) <= end_date
        )
    ).scalar() or 0.0
    
    # Count member payments as transactions
    current_transactions = db.query(func.count(MemberPayment.id)).join(Member).filter(
        and_(
            Member.business_id == current_business.id,
            func.date(MemberPayment.paid_at) >= start_date,
            func.date(MemberPayment.paid_at) <= end_date
        )
    ).scalar() or 0
    
    current_check_ins = db.query(func.count(AnalyticsEvent.id)).filter(
        and_(
            AnalyticsEvent.business_id == current_business.id,
            AnalyticsEvent.event_type == "check_in",
            func.date(AnalyticsEvent.event_timestamp) >= start_date,
            func.date(AnalyticsEvent.event_timestamp) <= end_date
        )
    ).scalar() or 0
    
    # Member statistics - Real data
    total_members = db.query(func.count(Member.id)).filter(
        Member.business_id == current_business.id
    ).scalar() or 0
    
    active_members = db.query(func.count(Member.id)).filter(
        and_(
            Member.business_id == current_business.id,
            Member.membership_status == "active"
        )
    ).scalar() or 0
    
    new_members = db.query(func.count(Member.id)).filter(
        and_(
            Member.business_id == current_business.id,
            func.date(Member.created_at) >= start_date,
            func.date(Member.created_at) <= end_date
        )
    ).scalar() or 0
    
    # Real peak hours data from check-ins
    peak_hours_data = db.query(
        func.extract('hour', AnalyticsEvent.event_timestamp).label('hour'),
        func.count(AnalyticsEvent.id).label('count')
    ).filter(
        and_(
            AnalyticsEvent.business_id == current_business.id,
            AnalyticsEvent.event_type == "check_in",
            func.date(AnalyticsEvent.event_timestamp) >= start_date,
            func.date(AnalyticsEvent.event_timestamp) <= end_date
        )
    ).group_by(func.extract('hour', AnalyticsEvent.event_timestamp)).all()
    
    # Format peak hours data
    peak_hours_list = [
        {"hour": f"{int(hour):02d}:00", "count": count}
        for hour, count in peak_hours_data
    ]
    
    # If no check-in data, use default structure
    if not peak_hours_list:
        peak_hours_list = []
    
    return DashboardMetrics(
        total_revenue=current_revenue,
        total_transactions=current_transactions,
        total_check_ins=current_check_ins,
        total_members=total_members,
        active_members=active_members,
        new_members=new_members,
        peak_usage_hours=peak_hours_list
    )

# Debug endpoint to check recent payments
@router.get("/debug/payments")
def debug_recent_payments(
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Debug endpoint to check recent member payments"""
    from app.models.member import MemberPayment
    
    # Get recent payments from last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    recent_payments = db.query(MemberPayment).join(Member).filter(
        and_(
            Member.business_id == current_business.id,
            func.date(MemberPayment.paid_at) >= start_date,
            func.date(MemberPayment.paid_at) <= end_date
        )
    ).limit(10).all()
    
    payments_data = []
    for payment in recent_payments:
        payments_data.append({
            "id": payment.id,
            "amount": float(payment.amount),
            "paid_at": payment.paid_at,
            "payment_method": payment.payment_method,
            "member_id": payment.member_id,
            "member_name": payment.member.full_name if payment.member else None
        })
    
    total_revenue = db.query(func.sum(MemberPayment.amount)).join(Member).filter(
        and_(
            Member.business_id == current_business.id,
            func.date(MemberPayment.paid_at) >= start_date,
            func.date(MemberPayment.paid_at) <= end_date
        )
    ).scalar() or 0.0
    
    total_transactions = db.query(func.count(MemberPayment.id)).join(Member).filter(
        and_(
            Member.business_id == current_business.id,
            func.date(MemberPayment.paid_at) >= start_date,
            func.date(MemberPayment.paid_at) <= end_date
        )
    ).scalar() or 0
    
    return {
        "total_revenue": float(total_revenue),
        "total_transactions": total_transactions,
        "recent_payments": payments_data,
        "business_id": current_business.id
    }

@router.get("/metrics", response_model=List[BusinessMetricsOut])
def get_business_metrics(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get daily business metrics"""
    query = db.query(BusinessMetrics).filter(
        BusinessMetrics.business_id == current_business.id
    )
    
    if date_from:
        query = query.filter(BusinessMetrics.date >= date_from)
    if date_to:
        query = query.filter(BusinessMetrics.date <= date_to)
    
    return query.order_by(BusinessMetrics.date.desc()).all()

# Admin Analytics Endpoints
@router.get("/checkins")
def get_checkin_analytics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get check-in analytics for admin dashboard"""
    try:
        from app.models.check_in import CheckIn
        
        # Build query for check-ins
        query = db.query(CheckIn)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(CheckIn.created_at >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(CheckIn.created_at <= end_dt)
        
        checkins = query.all()
        
        # Group by date for analytics
        checkin_data = []
        for checkin in checkins[:100]:  # Limit results for performance
            checkin_data.append({
                "id": checkin.id,
                "user_id": checkin.user_id,
                "business_id": checkin.business_id,
                "date": checkin.created_at.isoformat() if checkin.created_at else None
            })
        
        return {
            "total_checkins": len(checkins),
            "checkins": checkin_data
        }
    except Exception as e:
        return {
            "total_checkins": 0,
            "checkins": [],
            "error": str(e)
        }

@router.get("/payments") 
def get_payment_analytics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get payment analytics for admin dashboard"""
    try:
        from app.models.member import MemberPayment
        
        # Build query for payments
        query = db.query(MemberPayment)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(MemberPayment.payment_date >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(MemberPayment.payment_date <= end_dt)
        
        payments = query.all()
        
        # Format payment data
        payment_data = []
        for payment in payments[:100]:  # Limit results for performance
            payment_data.append({
                "id": payment.id,
                "amount": float(payment.amount),
                "member_id": payment.member_id,
                "date": payment.payment_date.isoformat() if payment.payment_date else None,
                "payment_method": getattr(payment, 'payment_method', 'unknown')
            })
        
        total_revenue = sum(float(p.amount) for p in payments)
        
        return {
            "total_payments": len(payments),
            "total_revenue": total_revenue,
            "payments": payment_data
        }
    except Exception as e:
        return {
            "total_payments": 0,
            "total_revenue": 0,
            "payments": [],
            "error": str(e)
        }
