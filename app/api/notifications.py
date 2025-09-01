from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas.notification import NotificationCreate, NotificationOut
from app.models.notification import Notification
from app.api.deps import get_current_user
from app.services.notification_service import NotificationService

router = APIRouter()
notification_service = NotificationService()

@router.get("/", response_model=List[NotificationOut])
async def get_notifications(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).all()

@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    return {"status": "success"}

@router.put("/read-all")
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"status": "success"}