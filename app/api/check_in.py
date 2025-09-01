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

router = APIRouter()

@router.post("/", response_model=QRCodeResponse)
def check_in(
    request: CheckInRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initiate check-in: verify flex credit and generate QR code for the center to scan.
    """
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