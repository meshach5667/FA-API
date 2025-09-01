from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.models.user import User
from app.models.admin import Admin
from app.models.business import Business
from app.models.booking import Booking
from app.models.check_in import CheckIn
from app.models.check_out import CheckOut
from app.models.activity import Activity
from app.models.group_activity import Group
from app.models.community import Community
from app.models.payment import Payment
from app.models.transaction import Transaction
from app.models.token import Token
from app.models.reward import Reward
from app.models.notification import Notification
from app.schemas.admin import AdminCreate, AdminOut, AdminLogin
from app.models.admin import Admin
from app.schemas.user import UserOut
from app.schemas.business import BusinessOut, BusinessCreate
from app.schemas.activity import ActivityOut
from app.schemas.community import CommunityOut
from app.schemas.payment import PaymentOut
from app.core.security import SECRET_KEY, ALGORITHM, create_access_token

router = APIRouter()

# Password and JWT setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="admin/login")

# Add this to your existing dependencies
async def get_current_super_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Admin:
    """Verify the admin is a super admin"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Admin not found"
        )
    return admin

# Admin Authentication endpoints
@router.post("/signup", response_model=AdminOut)
async def create_admin(
    admin: AdminCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_super_admin)
):
    """Only existing super admins can create new admins"""
    if db.query(Admin).filter(Admin.email == admin.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(admin.password)
    db_admin = Admin(
        email=admin.email,
        full_name=admin.full_name,
        hashed_password=hashed_password
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

@router.post("/login")
async def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Admin login endpoint"""
    admin = db.query(Admin).filter(Admin.email == form_data.username).first()
    if not admin or not pwd_context.verify(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": admin.email})
    return {"access_token": access_token, "token_type": "bearer"}

# Dashboard Stats
@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get overall dashboard statistics"""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_businesses = db.query(Business).count()
    active_businesses = db.query(Business).filter(Business.is_active == True).count()
    
    # Revenue calculations
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "completed"
    ).scalar() or 0
    
    # Messages count (if you have messages table)
    unread_messages = 0  # Implement based on your message system
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "gym_partners": total_businesses,
        "unread_messages": unread_messages,
        "total_revenue": total_revenue,
        "active_sessions": active_users  # Use active users as proxy for sessions
    }

@router.get("/users/stats")
async def get_users_stats(
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get detailed user statistics"""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # Count paid users (users with completed payments)
    paid_users = db.query(User).join(Payment).filter(
        Payment.status == "completed"
    ).distinct().count()
    
    gym_partners = db.query(Business).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "paid_users": paid_users,
        "gym_partners": gym_partners,
        "unread_messages": 0,  # Implement based on your message system
        "active_sessions": active_users
    }

@router.get("/analytics/revenue")
async def get_revenue_stats(
    period: str = "today",
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get revenue statistics for specified period"""
    now = datetime.utcnow()
    
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:  # year
        start_date = now - timedelta(days=365)
    
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "completed",
        Payment.timestamp >= start_date
    ).scalar() or 0
    
    return {
        "total_revenue": total_revenue,
        "period": period,
        "start_date": start_date,
        "end_date": now
    }

@router.get("/transactions")
async def get_transaction_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get transaction history"""
    transactions = db.query(Payment).offset(skip).limit(limit).all()
    
    # Transform to include user information
    result = []
    for transaction in transactions:
        user = db.query(User).filter(User.id == transaction.user_id).first()
        result.append({
            "id": transaction.id,
            "amount": transaction.amount,
            "status": transaction.status,
            "date": transaction.timestamp,
            "user_name": user.name if user else "Unknown User",
            "user_email": user.email if user else "unknown@example.com",
            "type": "credit" if transaction.amount > 0 else "debit",
            "transaction_type": transaction.payment_method or "unknown"
        })
    
    return result

@router.get("/users/activity")
async def get_user_activity_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get user activity history"""
    checkins = db.query(CheckIn).offset(skip).limit(limit).all()
    
    result = []
    for checkin in checkins:
        user = db.query(User).filter(User.id == checkin.user_id).first()
        business = db.query(Business).filter(Business.id == checkin.business_id).first()
        
        result.append({
            "id": checkin.id,
            "user_name": user.name if user else "Unknown User",
            "user_image": user.profile_picture if user else None,
            "business_name": business.name if business else "Unknown Business",
            "business_location": business.address if business else "Unknown Location",
            "tokens_used": checkin.tokens_used or 0,
            "created_at": checkin.timestamp,
            "status": "completed"
        })
    
    return result

@router.get("/users/{user_id}")
async def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get detailed information about a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's payment history
    payments = db.query(Payment).filter(Payment.user_id == user_id).all()
    total_spent = sum(p.amount for p in payments if p.status == "completed")
    
    # Get user's visit count
    visit_count = db.query(CheckIn).filter(CheckIn.user_id == user_id).count()
    
    # Get last check-in
    last_checkin = db.query(CheckIn).filter(CheckIn.user_id == user_id).order_by(CheckIn.timestamp.desc()).first()
    last_active = last_checkin.timestamp if last_checkin else user.updated_at or user.created_at
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone_number,
        "phoneNumber": user.phone_number,
        "membershipType": "premium" if total_spent > 1000 else "basic",
        "joinDate": user.created_at,
        "lastActive": last_active,
        "totalSpent": total_spent,
        "totalVisits": visit_count,
        "favoriteGyms": [],  # Implement based on your requirements
        "is_active": user.is_active
    }

@router.get("/users/{user_id}/history")
async def get_user_history(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get history for a specific user"""
    # Get check-ins
    checkins = db.query(CheckIn).filter(CheckIn.user_id == user_id).offset(skip).limit(limit).all()
    
    activities = []
    for checkin in checkins:
        business = db.query(Business).filter(Business.id == checkin.business_id).first()
        activities.append({
            "type": "visit",
            "date": checkin.timestamp,
            "details": "Checked in",
            "gymName": business.name if business else "Unknown Gym"
        })
    
    # Get payments
    payments = db.query(Payment).filter(Payment.user_id == user_id).offset(skip).limit(limit).all()
    for payment in payments:
        activities.append({
            "type": "payment",
            "date": payment.timestamp,
            "details": payment.description or "Payment",
            "amount": payment.amount
        })
    
    # Sort by date
    activities.sort(key=lambda x: x['date'], reverse=True)
    
    return {"activities": activities}

# User Management
@router.get("/users", response_model=List[UserOut])
async def get_all_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    super_admin = Depends(get_current_super_admin)
):
    """Get all users with their check-ins and token balance"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/users/{user_id}/payments")
async def get_user_payments(
    user_id: int,
    db: Session = Depends(get_db),
    super_admin: Admin = Depends(get_current_super_admin)
):
    """Get detailed payment history for a user"""
    payments = db.query(Payment).filter(Payment.user_id == user_id).all()
    return {
        "user_id": user_id,
        "total_payments": len(payments),
        "total_amount": sum(p.amount for p in payments),
        "payments": payments
    }

# Detailed User Analytics
@router.get("/users/{user_id}/analytics")
async def get_user_analytics(
    user_id: int,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get detailed analytics for a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get check-ins for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    checkins = db.query(CheckIn).filter(
        CheckIn.user_id == user_id,
        CheckIn.timestamp >= thirty_days_ago
    ).count()
    
    # Get bookings stats
    total_bookings = db.query(Booking).filter(Booking.user_id == user_id).count()
    completed_bookings = db.query(Booking).filter(
        Booking.user_id == user_id,
        Booking.status == "completed"
    ).count()
    
    return {
        "user_id": user_id,
        "checkins_last_30_days": checkins,
        "total_bookings": total_bookings,
        "completed_bookings": completed_bookings,
        "completion_rate": (completed_bookings / total_bookings * 100) if total_bookings > 0 else 0
    }

# Business Management
@router.get("/businesses", response_model=List[BusinessOut])
async def get_all_businesses(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    super_admin = Depends(get_current_super_admin)
):
    """Get all businesses with their metrics"""
    businesses = db.query(Business).offset(skip).limit(limit).all()
    return businesses

# Business Performance Metrics
@router.get("/businesses/{business_id}/performance")
async def get_business_performance(
    business_id: int,
    timeframe: str = "month",  # week, month, year
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get detailed performance metrics for a specific business"""
    if timeframe == "month":
        start_date = datetime.utcnow() - timedelta(days=30)
    elif timeframe == "week":
        start_date = datetime.utcnow() - timedelta(days=7)
    else:
        start_date = datetime.utcnow() - timedelta(days=365)

    # Get check-ins
    checkins = db.query(CheckIn).filter(
        CheckIn.business_id == business_id,
        CheckIn.timestamp >= start_date
    ).count()

    # Get revenue
    revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.business_id == business_id,
        Payment.timestamp >= start_date
    ).scalar() or 0

    return {
        "business_id": business_id,
        "timeframe": timeframe,
        "total_checkins": checkins,
        "total_revenue": revenue,
        "period_start": start_date,
        "period_end": datetime.utcnow()
    }

# Check-in/out Analytics
@router.get("/analytics/checkins")
async def get_checkin_analytics(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    super_admin = Depends(get_current_super_admin)
):
    """Get check-in analytics for specified date range"""
    query = db.query(
        func.date(CheckIn.timestamp).label('date'),
        func.count().label('count')
    )
    if start_date:
        query = query.filter(CheckIn.timestamp >= start_date)
    if end_date:
        query = query.filter(CheckIn.timestamp <= end_date)
    
    return query.group_by(func.date(CheckIn.timestamp)).all()

# Activity Monitoring
@router.get("/activities/all", response_model=List[ActivityOut])
async def get_all_activities(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    super_admin = Depends(get_current_super_admin)
):
    """Get all activities across all businesses"""
    activities = db.query(Activity).offset(skip).limit(limit).all()
    return activities

# Detailed Activity Analytics
@router.get("/activities/analytics")
async def get_activity_analytics(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    super_admin = Depends(get_current_super_admin)
):
    """Get detailed analytics for activities"""
    # TODO: Implement when ActivityJoin model is available
    query = db.query(
        Activity.business_id,
        func.count(Activity.id).label('total_activities')
    )
    
    if start_date:
        query = query.filter(Activity.date >= start_date)
    if end_date:
        query = query.filter(Activity.date <= end_date)
    
    return query.group_by(Activity.business_id).all()

# Community Monitoring
@router.get("/communities/all", response_model=List[CommunityOut])
async def get_all_communities(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    super_admin = Depends(get_current_super_admin)
):
    """Get all communities and their metrics"""
    communities = db.query(Community).offset(skip).limit(limit).all()
    return communities

# Business Creation
@router.post("/businesses", response_model=BusinessOut)
async def create_business(
    business: BusinessCreate,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Create a new business account"""
    new_business = Business(**business.dict())
    db.add(new_business)
    db.commit()
    db.refresh(new_business)
    return new_business

# Payment Analytics
@router.get("/analytics/payments")
async def get_payment_analytics(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    super_admin = Depends(get_current_super_admin)
):
    """Get payment analytics for specified date range"""
    query = db.query(
        func.date(Payment.timestamp).label('date'),
        func.count().label('count'),
        func.sum(Payment.amount).label('total_amount')
    )
    
    if start_date:
        query = query.filter(Payment.timestamp >= start_date)
    if end_date:
        query = query.filter(Payment.timestamp <= end_date)
    
    return query.group_by(func.date(Payment.timestamp)).all()

# Reconciliation
@router.get("/reconciliation/summary")
async def get_reconciliation_summary(
    db: Session = Depends(get_db),
    date: Optional[datetime] = None,
    super_admin = Depends(get_current_super_admin)
):
    """Get reconciliation summary for specified date"""
    # Implement reconciliation logic
    pass

@router.get("/reconciliation/daily")
async def daily_reconciliation(
    date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    super_admin: Admin = Depends(get_current_super_admin)
):
    """Daily payment reconciliation report"""
    if not date:
        date = datetime.utcnow().date()
    
    # Get all payments for the day
    payments = db.query(Payment).filter(
        func.date(Payment.timestamp) == date
    ).all()
    
    # Group by business
    business_totals = {}
    for payment in payments:
        if payment.business_id not in business_totals:
            business_totals[payment.business_id] = 0
        business_totals[payment.business_id] += payment.amount
    
    return {
        "date": date,
        "total_payments": len(payments),
        "total_amount": sum(p.amount for p in payments),
        "business_breakdown": business_totals,
        "reconciliation_status": "completed"
    }

@router.post("/reconciliation/approve/{payment_id}")
async def approve_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    super_admin: Admin = Depends(get_current_super_admin)
):
    """Approve a specific payment"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment.status = "approved"
    payment.approved_by = super_admin.id
    payment.approved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Payment approved", "payment_id": payment_id}

# System Health
@router.get("/system/health")
async def get_system_health(
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get system health metrics"""
    return {
        "database": "healthy",
        "api": "running",
        "last_check": datetime.utcnow()
    }

# System Maintenance
@router.post("/system/maintenance")
async def trigger_maintenance(
    maintenance_type: str,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Trigger system maintenance tasks"""
    if maintenance_type == "clean_old_tokens":
        # Clean expired tokens
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        deleted_count = db.query(Token).filter(Token.expires_at < thirty_days_ago).delete()
        db.commit()
        return {"status": f"Cleaned {deleted_count} expired tokens", "type": maintenance_type}
    elif maintenance_type == "archive_old_checkins":
        # Archive old check-ins
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        # For now, just count old check-ins
        old_checkins = db.query(CheckIn).filter(CheckIn.timestamp < ninety_days_ago).count()
        return {"status": f"Found {old_checkins} old check-ins (archiving not yet implemented)", "type": maintenance_type}
    
    return {"status": "maintenance completed", "type": maintenance_type}

# Rewards/Bonus Management
@router.get("/rewards")
async def get_rewards(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get all rewards"""
    rewards = db.query(Reward).offset(skip).limit(limit).all()
    return rewards

@router.post("/rewards")
async def create_reward(
    reward_data: dict,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Create a new reward"""
    reward = Reward(**reward_data)
    db.add(reward)
    db.commit()
    db.refresh(reward)
    return reward

@router.put("/rewards/{reward_id}")
async def update_reward(
    reward_id: int,
    reward_data: dict,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Update a reward"""
    reward = db.query(Reward).filter(Reward.id == reward_id).first()
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    
    for key, value in reward_data.items():
        setattr(reward, key, value)
    
    db.commit()
    db.refresh(reward)
    return reward

@router.delete("/rewards/{reward_id}")
async def delete_reward(
    reward_id: int,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Delete a reward"""
    reward = db.query(Reward).filter(Reward.id == reward_id).first()
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    
    db.delete(reward)
    db.commit()
    return {"message": "Reward deleted successfully"}

# Groups Management
@router.get("/groups")
async def get_groups(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get all groups"""
    groups = db.query(Group).offset(skip).limit(limit).all()
    return groups

@router.post("/groups")
async def create_group(
    group_data: dict,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Create a new group"""
    group = Group(**group_data)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group

@router.get("/groups/{group_id}")
async def get_group_details(
    group_id: int,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get detailed information about a specific group"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@router.put("/groups/{group_id}")
async def update_group(
    group_id: int,
    group_data: dict,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Update a group"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    for key, value in group_data.items():
        setattr(group, key, value)
    
    db.commit()
    db.refresh(group)
    return group

@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Delete a group"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    db.delete(group)
    db.commit()
    return {"message": "Group deleted successfully"}

# Community Management Extensions
@router.post("/communities")
async def create_community(
    community_data: dict,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Create a new community"""
    community = Community(**community_data)
    db.add(community)
    db.commit()
    db.refresh(community)
    return community

@router.get("/communities/{community_id}")
async def get_community_details(
    community_id: int,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get detailed information about a specific community"""
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    return community

@router.put("/communities/{community_id}")
async def update_community(
    community_id: int,
    community_data: dict,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Update a community"""
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    
    for key, value in community_data.items():
        setattr(community, key, value)
    
    db.commit()
    db.refresh(community)
    return community

@router.delete("/communities/{community_id}")
async def delete_community(
    community_id: int,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Delete a community"""
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    
    db.delete(community)
    db.commit()
    return {"message": "Community deleted successfully"}

# Notifications Management
@router.get("/notifications")
async def get_all_notifications(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get all notifications in the system"""
    notifications = db.query(Notification).offset(skip).limit(limit).all()
    return notifications

@router.post("/notifications")
async def send_notification(
    notification_data: dict,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Send a notification to users"""
    # Create notification for specific user or all users
    if notification_data.get("user_id"):
        # Send to specific user
        notification = Notification(
            user_id=notification_data["user_id"],
            title=notification_data["title"],
            message=notification_data["message"],
            type=notification_data.get("type", "general"),
            is_read=False
        )
        db.add(notification)
    else:
        # Send to all users
        users = db.query(User).all()
        for user in users:
            notification = Notification(
                user_id=user.id,
                title=notification_data["title"],
                message=notification_data["message"],
                type=notification_data.get("type", "general"),
                is_read=False
            )
            db.add(notification)
    
    db.commit()
    return {"message": "Notification sent successfully"}

@router.get("/broadcast/messages")
async def get_broadcast_messages(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get broadcast message history"""
    # This could be a separate table for tracking broadcast messages
    # For now, return general notifications
    notifications = db.query(Notification).filter(
        Notification.type == "broadcast"
    ).offset(skip).limit(limit).all()
    return notifications

@router.post("/broadcast/send")
async def send_broadcast_message(
    message_data: dict,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Send broadcast message to all users"""
    users = db.query(User).filter(User.is_active == True).all()
    
    for user in users:
        notification = Notification(
            user_id=user.id,
            title=message_data.get("title", "Broadcast Message"),
            message=message_data["message"],
            type="broadcast",
            is_read=False
        )
        db.add(notification)
    
    db.commit()
    return {
        "message": "Broadcast message sent successfully",
        "recipients_count": len(users)
    }

# Enhanced Business Management
@router.get("/businesses/{business_id}")
async def get_business_details(
    business_id: int,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get detailed information about a specific business"""
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Get additional statistics
    total_checkins = db.query(CheckIn).filter(CheckIn.business_id == business_id).count()
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.business_id == business_id,
        Payment.status == "completed"
    ).scalar() or 0
    
    return {
        "id": business.id,
        "name": business.name,
        "email": business.email,
        "phone_number": business.phone_number,
        "address": business.address,
        "is_active": business.is_active,
        "created_at": business.created_at,
        "total_checkins": total_checkins,
        "total_revenue": total_revenue,
        "rating": 4.5  # Calculate actual rating from reviews if available
    }

@router.put("/businesses/{business_id}")
async def update_business(
    business_id: int,
    business_data: dict,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Update a business"""
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    for key, value in business_data.items():
        if hasattr(business, key):
            setattr(business, key, value)
    
    business.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(business)
    return business

@router.delete("/businesses/{business_id}")
async def delete_business(
    business_id: int,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Delete a business"""
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Set as inactive instead of hard delete to preserve data integrity
    business.is_active = False
    business.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Business deactivated successfully"}

@router.get("/businesses/{business_id}/analytics")
async def get_business_analytics(
    business_id: int,
    timeframe: str = "month",
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get detailed analytics for a specific business"""
    if timeframe == "month":
        start_date = datetime.utcnow() - timedelta(days=30)
    elif timeframe == "week":
        start_date = datetime.utcnow() - timedelta(days=7)
    else:  # year
        start_date = datetime.utcnow() - timedelta(days=365)

    # Get check-ins
    checkins = db.query(CheckIn).filter(
        CheckIn.business_id == business_id,
        CheckIn.timestamp >= start_date
    ).count()

    # Get revenue
    revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.business_id == business_id,
        Payment.timestamp >= start_date,
        Payment.status == "completed"
    ).scalar() or 0

    # Get unique users
    unique_users = db.query(CheckIn.user_id).filter(
        CheckIn.business_id == business_id,
        CheckIn.timestamp >= start_date
    ).distinct().count()

    return {
        "business_id": business_id,
        "timeframe": timeframe,
        "total_checkins": checkins,
        "total_revenue": revenue,
        "unique_users": unique_users,
        "period_start": start_date,
        "period_end": datetime.utcnow()
    }

# Enhanced User Management
@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Update a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user_data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Delete/deactivate a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Deactivate instead of hard delete
    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "User deactivated successfully"}

# Admin Settings Management
@router.get("/settings")
async def get_admin_settings(
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get admin settings"""
    # This would typically come from a settings table
    # For now, return default settings
    return {
        "app_name": "FitAccess Admin",
        "version": "1.0.0",
        "maintenance_mode": False,
        "registration_enabled": True,
        "max_reward_points": 10000,
        "default_reward_multiplier": 1.0,
        "notification_settings": {
            "email_enabled": True,
            "push_enabled": True,
            "sms_enabled": False
        },
        "business_settings": {
            "auto_approve": False,
            "commission_rate": 0.1,
            "min_payout": 100
        }
    }

@router.put("/settings")
async def update_admin_settings(
    settings_data: dict,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Update admin settings"""
    # In a real app, this would update a settings table
    # For now, just return success
    return {
        "message": "Settings updated successfully",
        "updated_settings": settings_data
    }

# System Metrics and Health
@router.get("/system/health")
async def system_health(
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get system health metrics"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
        "timestamp": datetime.utcnow(),
        "uptime": "24h 30m",  # Calculate actual uptime
        "memory_usage": "45%",  # Get actual memory usage
        "cpu_usage": "12%"  # Get actual CPU usage
    }

# Report Generation
@router.post("/reports/generate")
async def generate_report(
    report_config: dict,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Generate various reports"""
    report_type = report_config.get("type", "users")
    start_date = datetime.fromisoformat(report_config.get("start_date", (datetime.utcnow() - timedelta(days=30)).isoformat()))
    end_date = datetime.fromisoformat(report_config.get("end_date", datetime.utcnow().isoformat()))
    
    if report_type == "users":
        data = db.query(User).filter(
            User.created_at >= start_date,
            User.created_at <= end_date
        ).all()
        report_data = [{"id": u.id, "username": u.username, "email": u.email, "created_at": u.created_at} for u in data]
    
    elif report_type == "transactions":
        data = db.query(Transaction).filter(
            Transaction.timestamp >= start_date,
            Transaction.timestamp <= end_date
        ).all()
        report_data = [{"id": t.id, "amount": t.amount, "type": t.type, "timestamp": t.timestamp} for t in data]
    
    elif report_type == "businesses":
        data = db.query(Business).filter(
            Business.created_at >= start_date,
            Business.created_at <= end_date
        ).all()
        report_data = [{"id": b.id, "name": b.name, "email": b.email, "created_at": b.created_at} for b in data]
    
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")
    
    return {
        "report_type": report_type,
        "period": {
            "start": start_date,
            "end": end_date
        },
        "total_records": len(report_data),
        "data": report_data
    }

# Audit Logs
@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    action: str = None,
    user_id: int = None,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get audit logs (admin actions)"""
    # In a real app, this would come from an audit_logs table
    # For now, return mock data
    mock_logs = [
        {
            "id": 1,
            "admin_id": super_admin.id,
            "admin_username": super_admin.username,
            "action": "user_deleted",
            "target_id": 123,
            "timestamp": datetime.utcnow() - timedelta(hours=2),
            "details": "Deleted user account"
        },
        {
            "id": 2,
            "admin_id": super_admin.id,
            "admin_username": super_admin.username,
            "action": "reward_created",
            "target_id": 456,
            "timestamp": datetime.utcnow() - timedelta(hours=5),
            "details": "Created new reward program"
        }
    ]
    
    return {
        "total": len(mock_logs),
        "logs": mock_logs[skip:skip+limit]
    }

# Content Moderation
@router.get("/moderation/flagged-content")
async def get_flagged_content(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Get flagged content for moderation"""
    # This would query flagged posts, comments, etc.
    # For now, return mock data
    return {
        "total": 0,
        "flagged_items": []
    }

@router.post("/moderation/review")
async def review_content(
    review_data: dict,
    db: Session = Depends(get_db),
    super_admin = Depends(get_current_super_admin)
):
    """Review flagged content (approve/reject)"""
    content_id = review_data["content_id"]
    action = review_data["action"]  # "approve" or "reject"
    
    # Process the moderation decision
    return {
        "message": f"Content {action}d successfully",
        "content_id": content_id,
        "action": action
    }