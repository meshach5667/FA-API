from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# Analytics Event schemas
class AnalyticsEventBase(BaseModel):
    event_type: str
    event_category: Optional[str] = None
    event_properties: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    ip_address: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None

class AnalyticsEventCreate(AnalyticsEventBase):
    pass

class AnalyticsEventOut(AnalyticsEventBase):
    id: int
    business_id: int
    user_id: Optional[int] = None
    event_timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Business Metrics schemas
class BusinessMetricsOut(BaseModel):
    id: int
    business_id: int
    date: date
    total_revenue: float
    total_bookings: int
    unique_users: int
    avg_session_duration: float
    total_check_ins: int
    total_events: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Dashboard Analytics
class DashboardMetrics(BaseModel):
    total_revenue: float
    total_transactions: int  # Changed from total_bookings to total_transactions
    total_check_ins: int
    # Member statistics
    total_members: int = 0
    active_members: int = 0
    new_members: int = 0
    # Real-time data
    peak_usage_hours: List[Dict[str, Any]] = []

# Revenue Analytics
class RevenueAnalytics(BaseModel):
    period_start: date
    period_end: date
    total_revenue: float
    subscription_revenue: float
    activity_revenue: float
    avg_transaction_value: float
    revenue_by_day: List[Dict[str, Any]] = []
    revenue_by_activity: List[Dict[str, Any]] = []
    payment_methods: List[Dict[str, Any]] = []

# User Analytics
class UserAnalytics(BaseModel):
    period_start: date
    period_end: date
    total_users: int
    new_users: int
    active_users: int
    returning_users: int
    user_retention_rate: float
    avg_session_duration: float
    users_by_location: List[Dict[str, Any]] = []
    users_by_device: List[Dict[str, Any]] = []
    user_growth_by_day: List[Dict[str, Any]] = []

# Activity Analytics
class ActivityAnalytics(BaseModel):
    period_start: date
    period_end: date
    total_activities: int
    active_activities: int
    avg_bookings_per_activity: float
    most_popular_activities: List[Dict[str, Any]] = []
    activity_revenue: List[Dict[str, Any]] = []
    activity_ratings: List[Dict[str, Any]] = []

# Conversion Funnel
class ConversionFunnel(BaseModel):
    period_start: date
    period_end: date
    total_visitors: int
    signed_up_users: int
    booked_activities: int
    completed_bookings: int
    signup_conversion_rate: float
    booking_conversion_rate: float
    completion_rate: float
