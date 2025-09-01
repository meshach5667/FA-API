from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.group_activity import GroupActivity
from app.schemas.group_activity import GroupActivityOut
from app.api.auth import get_current_user
from app.models.user import User
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.api.rewards import check_and_unlock_rewards

router = APIRouter()

class GroupActivityCreate(BaseModel):
    name: str
    date: Optional[datetime] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=list[GroupActivityOut])
def get_user_group_activities(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(GroupActivity).filter(
        (GroupActivity.user_id == current_user.id) | (GroupActivity.host_id == current_user.id)
    ).all()

@router.post("/", response_model=GroupActivityOut)
def create_group_activity(activity: GroupActivityCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_activity = GroupActivity(
        user_id=current_user.id,
        host_id=current_user.id,
        name=activity.name,
        date=activity.date or datetime.utcnow()
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    check_and_unlock_rewards(db, current_user)
    return db_activity

@router.get("/{activity_id}", response_model=GroupActivityOut)
def get_group_activity(activity_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    activity = db.query(GroupActivity).filter(
        GroupActivity.id == activity_id,
        (GroupActivity.user_id == current_user.id) | (GroupActivity.host_id == current_user.id)
    ).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Group activity not found")
    return activity

@router.put("/{activity_id}", response_model=GroupActivityOut)
def update_group_activity(activity_id: int, activity: GroupActivityCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_activity = db.query(GroupActivity).filter(
        GroupActivity.id == activity_id,
        GroupActivity.host_id == current_user.id
    ).first()
    if not db_activity:
        raise HTTPException(status_code=404, detail="Group activity not found or not host")
    db_activity.name = activity.name
    db_activity.date = activity.date or db_activity.date
    db.commit()
    db.refresh(db_activity)
    check_and_unlock_rewards(db, current_user)
    return db_activity

@router.delete("/{activity_id}")
def delete_group_activity(activity_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_activity = db.query(GroupActivity).filter(
        GroupActivity.id == activity_id,
        GroupActivity.host_id == current_user.id
    ).first()
    if not db_activity:
        raise HTTPException(status_code=404, detail="Group activity not found or not host")
    db.delete(db_activity)
    db.commit()
    check_and_unlock_rewards(db, current_user)
    return {"detail": "Group activity deleted"}