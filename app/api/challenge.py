from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.challenge import MonthlyChallenge
from app.schemas.challenge import MonthlyChallengeOut
from app.api.auth import get_current_user
from app.models.user import User
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.api.rewards import check_and_unlock_rewards

router = APIRouter()

class MonthlyChallengeCreate(BaseModel):
    name: str
    completed: bool = False
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=list[MonthlyChallengeOut])
def get_user_challenges(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(MonthlyChallenge).filter_by(user_id=current_user.id).all()

@router.post("/", response_model=MonthlyChallengeOut)
def create_challenge(challenge: MonthlyChallengeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_challenge = MonthlyChallenge(
        user_id=current_user.id,
        name=challenge.name,
        completed=challenge.completed,
        completed_at=challenge.completed_at
    )
    db.add(db_challenge)
    db.commit()
    db.refresh(db_challenge)
    check_and_unlock_rewards(db, current_user)
    return db_challenge

@router.get("/{challenge_id}", response_model=MonthlyChallengeOut)
def get_challenge(challenge_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    challenge = db.query(MonthlyChallenge).filter_by(id=challenge_id, user_id=current_user.id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge

@router.put("/{challenge_id}", response_model=MonthlyChallengeOut)
def update_challenge(challenge_id: int, challenge: MonthlyChallengeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_challenge = db.query(MonthlyChallenge).filter_by(id=challenge_id, user_id=current_user.id).first()
    if not db_challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    db_challenge.name = challenge.name
    db_challenge.completed = challenge.completed
    db_challenge.completed_at = challenge.completed_at
    db.commit()
    db.refresh(db_challenge)
    check_and_unlock_rewards(db, current_user)
    return db_challenge

@router.delete("/{challenge_id}")
def delete_challenge(challenge_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_challenge = db.query(MonthlyChallenge).filter_by(id=challenge_id, user_id=current_user.id).first()
    if not db_challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    db.delete(db_challenge)
    db.commit()
    check_and_unlock_rewards(db, current_user)
    return {"detail": "Challenge deleted"}