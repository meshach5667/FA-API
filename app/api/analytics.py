from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, Integer
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
    """Get key metrics for the analytics dashboard"""
    end_date = date.today()
    start_date = end_date - timedelta(days=period_days)
    
    # Previous period for comparison
    prev_end_date = start_date - timedelta(days=1)
    prev_start_date = prev_end_date - timedelta(days=period_days)
    
    # Current period metrics
    current_revenue = db.query(func.sum(Payment.amount)).filter(
        and_(
            Payment.business_id == current_business.id,
            func.date(Payment.created_at) >= start_date,
            func.date(Payment.created_at) <= end_date,
            Payment.status == "completed"
        )
    ).scalar() or 0.0
    
    current_bookings = db.query(func.count(Booking.id)).filter(
        and_(
            Booking.business_id == current_business.id,
            func.date(Booking.created_at) >= start_date,
            func.date(Booking.created_at) <= end_date
        )
    ).scalar() or 0
    
    current_users = db.query(func.count(func.distinct(AnalyticsEvent.user_id))).filter(
        and_(
            AnalyticsEvent.business_id == current_business.id,
            func.date(AnalyticsEvent.event_timestamp) >= start_date,
            func.date(AnalyticsEvent.event_timestamp) <= end_date,
            AnalyticsEvent.user_id.isnot(None)
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
    
    # Member statistics
    total_members = db.query(func.count(Member.id)).filter(
        Member.business_id == current_business.id
    ).scalar() or 0
    
    active_members = db.query(func.count(Member.id)).filter(
        and_(
            Member.business_id == current_business.id,
            func.date(Member.created_at) >= start_date - timedelta(days=90)  # Active in last 90 days
        )
    ).scalar() or 0
    
    new_members = db.query(func.count(Member.id)).filter(
        and_(
            Member.business_id == current_business.id,
            func.date(Member.created_at) >= start_date,
            func.date(Member.created_at) <= end_date
        )
    ).scalar() or 0
    
    # Payment status statistics
    paid_invoices = db.query(func.count(MemberInvoice.id)).filter(
        and_(
            MemberInvoice.is_paid == True,
            MemberInvoice.member_id == Member.id,
            Member.business_id == current_business.id,
            func.date(MemberInvoice.paid_at) >= start_date,
            func.date(MemberInvoice.paid_at) <= end_date
        )
    ).scalar() or 0
    
    pending_payments = db.query(func.count(MemberInvoice.id)).filter(
        and_(
            MemberInvoice.is_paid == False,
            MemberInvoice.member_id == Member.id,
            Member.business_id == current_business.id
        )
    ).scalar() or 0
    
    # Previous period metrics for growth calculation
    prev_revenue = db.query(func.sum(Payment.amount)).filter(
        and_(
            Payment.business_id == current_business.id,
            func.date(Payment.created_at) >= prev_start_date,
            func.date(Payment.created_at) <= prev_end_date,
            Payment.status == "completed"
        )
    ).scalar() or 0.0
    
    prev_bookings = db.query(func.count(Booking.id)).filter(
        and_(
            Booking.business_id == current_business.id,
            func.date(Booking.created_at) >= prev_start_date,
            func.date(Booking.created_at) <= prev_end_date
        )
    ).scalar() or 0
    
    prev_users = db.query(func.count(func.distinct(AnalyticsEvent.user_id))).filter(
        and_(
            AnalyticsEvent.business_id == current_business.id,
            func.date(AnalyticsEvent.event_timestamp) >= prev_start_date,
            func.date(AnalyticsEvent.event_timestamp) <= prev_end_date,
            AnalyticsEvent.user_id.isnot(None)
        )
    ).scalar() or 0
    
    prev_check_ins = db.query(func.count(AnalyticsEvent.id)).filter(
        and_(
            AnalyticsEvent.business_id == current_business.id,
            AnalyticsEvent.event_type == "check_in",
            func.date(AnalyticsEvent.event_timestamp) >= prev_start_date,
            func.date(AnalyticsEvent.event_timestamp) <= prev_end_date
        )
    ).scalar() or 0
    
    # Calculate growth rates
    revenue_growth = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    bookings_growth = ((current_bookings - prev_bookings) / prev_bookings * 100) if prev_bookings > 0 else 0
    users_growth = ((current_users - prev_users) / prev_users * 100) if prev_users > 0 else 0
    check_ins_growth = ((current_check_ins - prev_check_ins) / prev_check_ins * 100) if prev_check_ins > 0 else 0
    
    # Top activities by bookings and joins (without date filter for better data)
    top_activities_query = db.query(
        Activity.id,
        Activity.name,
        Activity.activity_type,
        func.count(Booking.id).label('booking_count'),
        func.coalesce(Activity.join_count, 0).label('join_count')
    ).outerjoin(
        Booking, Activity.id == Booking.activity_id
    ).filter(
        Activity.business_id == current_business.id
    ).group_by(
        Activity.id, Activity.name, Activity.activity_type, Activity.join_count
    ).order_by(
        desc(func.count(Booking.id) + func.coalesce(Activity.join_count, 0))
    ).limit(5).all()
    
    # If no activities with bookings/joins, get all activities from the business
    if not top_activities_query:
        top_activities_query = db.query(
            Activity.id,
            Activity.name,
            Activity.activity_type,
            func.cast(0, Integer).label('booking_count'),
            func.coalesce(Activity.join_count, 0).label('join_count')
        ).filter(
            Activity.business_id == current_business.id
        ).order_by(desc(Activity.created_at)).limit(5).all()
    
    top_activities_list = [
        {
            "id": activity.id,
            "name": activity.name,
            "type": activity.activity_type or "General",
            "bookings": activity.booking_count,
            "joins": activity.join_count,
            "total_engagement": activity.booking_count + activity.join_count
        }
        for activity in top_activities_query
    ]
    
    top_locations_list = []
    peak_hours_list = []
    
    return DashboardMetrics(
        total_revenue=current_revenue,
        total_bookings=current_bookings,
        total_users=current_users,
        total_check_ins=current_check_ins,
        revenue_growth=revenue_growth,
        bookings_growth=bookings_growth,
        users_growth=users_growth,
        check_ins_growth=check_ins_growth,
        total_members=total_members,
        active_members=active_members,
        new_members=new_members,
        paid_invoices=paid_invoices,
        pending_payments=pending_payments,
        top_activities=top_activities_list,
        top_user_locations=top_locations_list,
        peak_usage_hours=peak_hours_list
    )

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
