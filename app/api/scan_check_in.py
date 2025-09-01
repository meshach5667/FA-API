from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from app.models.user import User
from app.models.center import Center
from app.models.scan_check_in import ScanCheckIn
from app.db.database import get_db
from app.schemas.scan_check_in import ScanCheckInRequest, ScanCheckInResponse, ScanCheckInHistoryOut

router = APIRouter()

@router.post("/", response_model=ScanCheckInResponse)
def scan_check_in(
    data: ScanCheckInRequest,
    db: Session = Depends(get_db)
):
    """
    Center scans user's QR code, checks and deducts flex credit, confirms check-in, and records it.
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
    scan_check_in_record = ScanCheckIn(user_id=user.id, center_id=center.id, timestamp=datetime.fromisoformat(data.timestamp))
    db.add(scan_check_in_record)
    db.commit()
    return ScanCheckInResponse(
        message="Scan check-in successful. User access granted.",
        remaining_flex_credit=user.flex_credit
    )

@router.get("/history/{user_id}", response_model=List[ScanCheckInHistoryOut])
def get_scan_check_in_history(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get scan check-in history for a user.
    """
    records = db.query(ScanCheckIn).filter(ScanCheckIn.user_id == user_id).order_by(ScanCheckIn.timestamp.desc()).all()
    return [
        ScanCheckInHistoryOut(
            center_id=record.center_id,
            timestamp=record.timestamp
        )
        for record in records
    ]