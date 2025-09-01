from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app.models.user import User
from app.models.center import Center
from app.models.scan_check_out import ScanCheckOut
from app.db.database import get_db
from app.schemas.scan_check_out import ScanCheckOutRequest, ScanCheckOutResponse, ScanCheckOutHistoryOut

router = APIRouter()

@router.post("/", response_model=ScanCheckOutResponse)
def scan_check_out(
    data: ScanCheckOutRequest,
    db: Session = Depends(get_db)
):
    """
    Center scans user's QR code to check out the user and records it.
    """
    user = db.query(User).filter(User.id == data.user_id).first()
    center = db.query(Center).filter(Center.id == data.center_id).first()
    if not user or not center:
        raise HTTPException(status_code=404, detail="User or Center not found")
    scan_check_out_record = ScanCheckOut(
        user_id=user.id,
        center_id=center.id,
        timestamp=datetime.fromisoformat(data.timestamp)
    )
    db.add(scan_check_out_record)
    db.commit()
    return ScanCheckOutResponse(
        message="Scan check-out successful. User has left the center."
    )

@router.get("/history/{user_id}", response_model=List[ScanCheckOutHistoryOut])
def get_scan_check_out_history(
    user_id: int,
    start_date: Optional[datetime] = Query(None, description="Filter from this date (inclusive)"),
    end_date: Optional[datetime] = Query(None, description="Filter up to this date (inclusive)"),
    db: Session = Depends(get_db)
):
    """
    Get scan check-out history for a user, with center details and optional date filtering.
    """
    query = db.query(ScanCheckOut).join(Center, ScanCheckOut.center_id == Center.id).filter(ScanCheckOut.user_id == user_id)
    if start_date:
        query = query.filter(ScanCheckOut.timestamp >= start_date)
    if end_date:
        query = query.filter(ScanCheckOut.timestamp <= end_date)
    records = query.order_by(ScanCheckOut.timestamp.desc()).all()
    return [
        ScanCheckOutHistoryOut(
            center_id=record.center.id,
            center_name=record.center.name,
            address=record.center.address,
            state=record.center.state,
            timestamp=record.timestamp
        )
        for record in records
    ]