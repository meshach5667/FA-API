from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app.models.user import User
from app.models.center import Center
from app.models.check_out import CheckOut
from app.db.database import get_db
from app.api.auth import get_current_user
from app.schemas.check_out import CheckOutRequest, CheckOutQRCodeResponse, CheckOutScanConfirmRequest, CheckOutHistoryCenterOut
import qrcode
import io
import base64

router = APIRouter()

@router.post("/", response_model=CheckOutQRCodeResponse)
def check_out(
    request: CheckOutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a check-out QR code and log the check-out.
    Supports both user and member check-out.
    """
    from app.models.member import Member
    from app.models.check_in import CheckIn
    
    # Handle member check-out (for business interface)
    if hasattr(request, 'member_id') and request.member_id:
        member = db.query(Member).filter(Member.id == request.member_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Find and update the active check-in record
        active_checkin = db.query(CheckIn).filter(
            CheckIn.member_id == member.id,
            CheckIn.status == "active"
        ).first()
        
        if not active_checkin:
            raise HTTPException(status_code=400, detail="No active check-in found for this member")
        
        # Update check-in status to completed
        active_checkin.status = "completed"
        
        # Create check-out record
        check_out_record = CheckOut(
            user_id=None,
            member_id=member.id,
            center_id=request.center_id
        )
        db.add(check_out_record)
        db.commit()
        
        return CheckOutQRCodeResponse(
            message=f"Member {member.first_name} {member.last_name} checked out successfully",
            qr_code_base64=""  # No QR needed for direct member check-out
        )
    
    # Handle user check-out (original functionality)
    user = db.query(User).filter(User.id == current_user.id).first()
    center = db.query(Center).filter(Center.id == request.center_id).first()
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")

    # Generate QR code with user ID, center ID, and timestamp
    payload = {
        "user_id": user.id,
        "center_id": center.id,
        "timestamp": datetime.utcnow().isoformat()
    }
    qr_data = f"{payload['user_id']}|{payload['center_id']}|{payload['timestamp']}|CHECKED_OUT"
    qr_img = qrcode.make(qr_data)
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    # Log the check-out
    check_out_record = CheckOut(user_id=user.id, center_id=center.id)
    db.add(check_out_record)
    db.commit()

    return CheckOutQRCodeResponse(
        message="Check-out successful. Show this QR code at the center.",
        qr_code_base64=qr_base64
    )

@router.post("/scan-confirm")
def confirm_check_out_scan(
    data: CheckOutScanConfirmRequest,
    db: Session = Depends(get_db)
):
    """
    Confirm QR scan at center and finalize check-out.
    """
    user = db.query(User).filter(User.id == data.user_id).first()
    center = db.query(Center).filter(Center.id == data.center_id).first()
    if not user or not center:
        raise HTTPException(status_code=404, detail="User or Center not found")
    # Optionally, you can update a status or log the confirmation here
    return {
        "message": "Check-out scan confirmed.",
        "user_id": user.id,
        "center_id": center.id,
        "timestamp": data.timestamp
    }

@router.get("/history/{user_id}", response_model=List[CheckOutHistoryCenterOut])
def get_check_out_history(
    user_id: int,
    start_date: Optional[datetime] = Query(None, description="Filter from this date (inclusive)"),
    end_date: Optional[datetime] = Query(None, description="Filter up to this date (inclusive)"),
    db: Session = Depends(get_db)
):
    """
    Get check-out history for a user, with center details and optional date filtering.
    """
    query = db.query(CheckOut).join(Center, CheckOut.center_id == Center.id).filter(CheckOut.user_id == user_id)
    if start_date:
        query = query.filter(CheckOut.timestamp >= start_date)
    if end_date:
        query = query.filter(CheckOut.timestamp <= end_date)
    records = query.order_by(CheckOut.timestamp.desc()).all()
    return [
        CheckOutHistoryCenterOut(
            center_id=record.center.id,
            center_name=record.center.name,
            address=record.center.address,
            state=record.center.state,
            timestamp=record.timestamp
        )
        for record in records
    ]