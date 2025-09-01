from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_
from typing import List, Optional
from datetime import datetime, date, time, timedelta
from app.db.database import get_db
from app.models.schedule import Schedule
from app.models.booking import Booking
from app.schemas.schedule import (
    ScheduleCreate, ScheduleOut, ScheduleUpdate,
    ScheduleSearch, ScheduleAvailability
)
from app.api.deps import get_current_business, get_current_user

router = APIRouter()

@router.post("/", response_model=ScheduleOut)
def create_schedule(
    schedule_data: ScheduleCreate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Create a new schedule"""
    schedule = Schedule(
        business_id=current_business.id,
        **schedule_data.dict()
    )
    
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule

@router.get("/", response_model=List[ScheduleOut])
def get_schedules(
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    activity_id: Optional[int] = Query(None),
    limit: int = Query(50, le=100)
):
    """Get schedules for the current business with optional filters"""
    query = db.query(Schedule).filter(Schedule.business_id == current_business.id)
    
    if date_from:
        query = query.filter(func.date(Schedule.start_time) >= date_from)
    if date_to:
        query = query.filter(func.date(Schedule.start_time) <= date_to)
    if activity_id:
        query = query.filter(Schedule.activity_id == activity_id)
    
    return query.order_by(Schedule.start_time).limit(limit).all()

@router.get("/{schedule_id}", response_model=ScheduleOut)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get a specific schedule by ID"""
    schedule = db.query(Schedule).filter(
        and_(
            Schedule.id == schedule_id,
            Schedule.business_id == current_business.id
        )
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return schedule

@router.put("/{schedule_id}", response_model=ScheduleOut)
def update_schedule(
    schedule_id: int,
    schedule_update: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Update a schedule"""
    schedule = db.query(Schedule).filter(
        and_(
            Schedule.id == schedule_id,
            Schedule.business_id == current_business.id
        )
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    for field, value in schedule_update.dict(exclude_unset=True).items():
        setattr(schedule, field, value)
    
    db.commit()
    db.refresh(schedule)
    return schedule

@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Delete a schedule"""
    schedule = db.query(Schedule).filter(
        and_(
            Schedule.id == schedule_id,
            Schedule.business_id == current_business.id
        )
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted successfully"}

@router.get("/{schedule_id}/availability", response_model=ScheduleAvailability)
def get_schedule_availability(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get availability information for a specific schedule"""
    schedule = db.query(Schedule).filter(
        and_(
            Schedule.id == schedule_id,
            Schedule.business_id == current_business.id
        )
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Count current bookings
    current_bookings = db.query(func.count(Booking.id)).filter(
        Booking.schedule_id == schedule_id
    ).scalar() or 0
    
    available_spots = max(0, schedule.capacity - current_bookings)
    is_available = available_spots > 0 and schedule.start_time > datetime.now()
    
    return ScheduleAvailability(
        schedule_id=schedule_id,
        total_capacity=schedule.capacity,
        current_bookings=current_bookings,
        available_spots=available_spots,
        is_available=is_available,
        start_time=schedule.start_time,
        end_time=schedule.end_time
    )

@router.post("/{schedule_id}/book")
def book_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    current_user = Depends(get_current_user)
):
    """Book a spot in a schedule"""
    schedule = db.query(Schedule).filter(
        and_(
            Schedule.id == schedule_id,
            Schedule.business_id == current_business.id
        )
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Check if schedule is in the future
    if schedule.start_time <= datetime.now():
        raise HTTPException(status_code=400, detail="Cannot book past schedules")
    
    # Check availability
    current_bookings = db.query(func.count(Booking.id)).filter(
        Booking.schedule_id == schedule_id
    ).scalar() or 0
    
    if current_bookings >= schedule.capacity:
        raise HTTPException(status_code=400, detail="Schedule is fully booked")
    
    # Check if user already booked
    existing_booking = db.query(Booking).filter(
        and_(
            Booking.schedule_id == schedule_id,
            Booking.user_id == current_user.id
        )
    ).first()
    
    if existing_booking:
        raise HTTPException(status_code=400, detail="You have already booked this schedule")
    
    # Create booking
    booking = Booking(
        user_id=current_user.id,
        business_id=current_business.id,
        schedule_id=schedule_id,
        activity_id=schedule.activity_id,
        status="confirmed"
    )
    
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    return {"message": "Schedule booked successfully", "booking_id": booking.id}

@router.get("/search/available", response_model=List[ScheduleOut])
def search_available_schedules(
    date: Optional[date] = Query(None, description="Search for specific date"),
    time_from: Optional[time] = Query(None, description="Search from specific time"),
    time_to: Optional[time] = Query(None, description="Search until specific time"),
    activity_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Search for available schedules"""
    query = db.query(Schedule).filter(
        and_(
            Schedule.business_id == current_business.id,
            Schedule.start_time > datetime.now()  # Only future schedules
        )
    )
    
    if date:
        query = query.filter(func.date(Schedule.start_time) == date)
    if time_from:
        query = query.filter(func.time(Schedule.start_time) >= time_from)
    if time_to:
        query = query.filter(func.time(Schedule.start_time) <= time_to)
    if activity_id:
        query = query.filter(Schedule.activity_id == activity_id)
    
    schedules = query.order_by(Schedule.start_time).all()
    
    # Filter out fully booked schedules
    available_schedules = []
    for schedule in schedules:
        current_bookings = db.query(func.count(Booking.id)).filter(
            Booking.schedule_id == schedule.id
        ).scalar() or 0
        
        if current_bookings < schedule.capacity:
            available_schedules.append(schedule)
    
    return available_schedules
