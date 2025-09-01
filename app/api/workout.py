from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.workout import Workout
from app.schemas.workout import WorkoutOut
from app.api.auth import get_current_user
from app.models.user import User
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.api.rewards import check_and_unlock_rewards

router = APIRouter()

class WorkoutCreate(BaseModel):
    type: str
    start_time: Optional[datetime] = None
    duration_minutes: int = 0
    with_friends: bool = False

    class Config:
        from_attributes = True

@router.get("/", response_model=list[WorkoutOut])
def get_user_workouts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Workout).filter_by(user_id=current_user.id).all()

@router.post("/", response_model=WorkoutOut)
def create_workout(workout: WorkoutCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_workout = Workout(
        user_id=current_user.id,
        type=workout.type,
        start_time=workout.start_time or datetime.utcnow(),
        duration_minutes=workout.duration_minutes,
        with_friends=workout.with_friends
    )
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    check_and_unlock_rewards(db, current_user)
    return db_workout

@router.get("/{workout_id}", response_model=WorkoutOut)
def get_workout(workout_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    workout = db.query(Workout).filter_by(id=workout_id, user_id=current_user.id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout

@router.put("/{workout_id}", response_model=WorkoutOut)
def update_workout(workout_id: int, workout: WorkoutCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_workout = db.query(Workout).filter_by(id=workout_id, user_id=current_user.id).first()
    if not db_workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    db_workout.type = workout.type
    db_workout.start_time = workout.start_time or db_workout.start_time
    db_workout.duration_minutes = workout.duration_minutes
    db_workout.with_friends = workout.with_friends
    db.commit()
    db.refresh(db_workout)
    check_and_unlock_rewards(db, current_user)
    return db_workout

@router.delete("/{workout_id}")
def delete_workout(workout_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_workout = db.query(Workout).filter_by(id=workout_id, user_id=current_user.id).first()
    if not db_workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    db.delete(db_workout)
    db.commit()
    check_and_unlock_rewards(db, current_user)
    return {"detail": "Workout deleted"}