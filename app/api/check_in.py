from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app.models.user import User
from app.models.center import Center
from app.db.database import get_db
from app.api.auth import get_current_user
from app.schemas.check_in import CheckInRequest, QRCodeResponse, ScanConfirmRequest, CheckInHistoryCenterOut
import qrcode
import io
import base64
from app.models.check_in import CheckIn
from app.models.analytics import AnalyticsEvent

router = APIRouter()

@router.post("/", response_model=QRCodeResponse)
def check_in(
    request: CheckInRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initiate check-in: verify flex credit and generate QR code for the center to scan.
    Supports both user and member check-ins.
    """
    from app.models.member import Member
    from app.api.deps import get_current_business
    
    # Handle member check-in (for business interface)
    if hasattr(request, 'member_id') and request.member_id:
        # This should be called from business interface
        member = db.query(Member).filter(Member.id == request.member_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        if not member.is_active:
            raise HTTPException(status_code=400, detail="Member is not active")
        
        # Create check-in record for member
        check_in_record = CheckIn(
            user_id=None,
            member_id=member.id,
            center_id=request.center_id,
            check_in_time=datetime.utcnow(),
            status="active"
        )
        db.add(check_in_record)
        
        # Track analytics
        analytics_event = AnalyticsEvent(
            business_id=member.business_id,
            event_type="check_in",
            event_category="member_activity",
            event_properties={
                "member_id": member.id,
                "member_name": f"{member.first_name} {member.last_name}",
                "center_id": request.center_id
            },
            event_timestamp=datetime.utcnow()
        )
        db.add(analytics_event)
        
        db.commit()
        db.refresh(check_in_record)
        
        return QRCodeResponse(
            message=f"Member {member.first_name} {member.last_name} checked in successfully",
            qr_code_base64=""  # No QR needed for direct member check-in
        )
    
    # Handle user check-in (original functionality)
    user = db.query(User).filter(User.id == current_user.id).first()
    center = db.query(Center).filter(Center.id == request.center_id).first()
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")
    if user.flex_credit < center.credit_required:
        raise HTTPException(
            status_code=402,
            detail="Insufficient flex credit. Please top up to check in."
        )
    # Generate QR code with user ID, center ID, and timestamp
    payload = {
        "user_id": user.id,
        "center_id": center.id,
        "timestamp": datetime.utcnow().isoformat()
    }
    qr_data = f"{payload['user_id']}|{payload['center_id']}|{payload['timestamp']}"
    qr_img = qrcode.make(qr_data)
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return QRCodeResponse(
        message="Check-in allowed. Show this QR code at the center.",
        qr_code_base64=qr_base64
    )

@router.get("/current")
def get_current_checked_in_members(
    db: Session = Depends(get_db)
):
    """Get currently checked-in members (business interface)"""
    from app.models.member import Member
    from app.api.deps import get_current_business
    from app.models.business import Business
    
    try:
        # For now, we'll get all businesses since auth might not be set up properly
        current_checkins = db.query(CheckIn).filter(
            CheckIn.status == "active",
            CheckIn.member_id.isnot(None)
        ).all()
        
        checked_in_members = []
        for checkin in current_checkins:
            if checkin.member:
                checked_in_members.append({
                    "id": checkin.id,
                    "member_id": checkin.member.id,
                    "member_name": f"{checkin.member.first_name} {checkin.member.last_name}",
                    "member_email": checkin.member.email,
                    "check_in_time": checkin.check_in_time.isoformat(),
                    "membership_type": checkin.member.membership_type,
                    "is_active": checkin.member.is_active
                })
        
        return checked_in_members
        
    except Exception as e:
        # Return empty list if there's an error
        return []

@router.post("/scan-confirm")
def confirm_scan(
    data: ScanConfirmRequest,
    db: Session = Depends(get_db)
):
    """
    Confirm QR scan at center and deduct flex credit.
    """
    user = db.query(User).filter(User.id == data.user_id).first()
    center = db.query(Center).filter(Center.id == data.center_id).first()
    if not user or not center:
        raise HTTPException(status_code=404, detail="User or Center not found")
    if user.flex_credit < center.credit_required:
        raise HTTPException(
            status_code=402,
            detail="Insufficient flex credit. Please top up."
        )
    user.flex_credit -= center.credit_required
    check_in_record = CheckIn(user_id=user.id, center_id=center.id)
    db.add(check_in_record)
    
    # Track analytics event for check-in
    analytics_event = AnalyticsEvent(
        business_id=center.business_id if hasattr(center, 'business_id') else None,
        user_id=user.id,
        event_type="check_in",
        event_category="facility_usage",
        event_properties={"center_id": center.id, "center_name": center.name}
    )
    db.add(analytics_event)
    
    db.commit()
    return {
        "message": "Check-in confirmed and credit deducted.",
        "remaining_flex_credit": user.flex_credit
    }

@router.get("/history/{user_id}", response_model=List[CheckInHistoryCenterOut])
def get_check_in_history(
    user_id: int,
    start_date: Optional[datetime] = Query(None, description="Filter from this date (inclusive)"),
    end_date: Optional[datetime] = Query(None, description="Filter up to this date (inclusive)"),
    db: Session = Depends(get_db)
):
    """
    Get check-in history for a user, with center details and optional date filtering.
    """
    query = db.query(CheckIn).join(Center, CheckIn.center_id == Center.id).filter(CheckIn.user_id == user_id)
    if start_date:
        query = query.filter(CheckIn.timestamp >= start_date)
    if end_date:
        query = query.filter(CheckIn.timestamp <= end_date)
    records = query.order_by(CheckIn.timestamp.desc()).all()
    return [
        CheckInHistoryCenterOut(
            center_id=record.center.id,
            center_name=record.center.name,
            address=record.center.address,
            state=record.center.state,
            timestamp=record.timestamp
        )
        for record in records
    ]