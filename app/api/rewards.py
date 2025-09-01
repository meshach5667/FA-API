from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.reward import Reward, UserReward
from app.api.auth import get_current_user
from app.models.user import User
from app.schemas.reward import RewardOut, UserRewardOut, UserPointsOut
from app.models.check_in import CheckIn
from app.models.payment import Payment
from app.models.workout import Workout
from app.models.group_activity import GroupActivity
from app.models.challenge import MonthlyChallenge
from sqlalchemy import func, extract
from app.schemas.reward import RewardOut
from pydantic import BaseModel

class RewardCreate(BaseModel):
    name: str
    description: str
    points_required: int
    category: str
    reward_type: str
    reward_value: float
    reward_description: str

    class Config:
        from_attributes = True

class RewardUpdate(RewardCreate):
    pass

router = APIRouter()
@router.post("/", response_model=RewardOut)
def create_reward(reward: RewardCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_reward = Reward(**reward.dict())
    db.add(db_reward)
    db.commit()
    db.refresh(db_reward)
    return db_reward

@router.put("/{reward_id}", response_model=RewardOut)
def update_reward(reward_id: int, reward: RewardUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_reward = db.query(Reward).filter_by(id=reward_id).first()
    if not db_reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    for key, value in reward.dict().items():
        setattr(db_reward, key, value)
    db.commit()
    db.refresh(db_reward)
    return db_reward

@router.delete("/{reward_id}")
def delete_reward(reward_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_reward = db.query(Reward).filter_by(id=reward_id).first()
    if not db_reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    db.delete(db_reward)
    db.commit()
    return {"detail": "Reward deleted"}
@router.get("/available", response_model=list[RewardOut])
def get_available_rewards(db: Session = Depends(get_db)):
    return db.query(Reward).all()

@router.get("/user", response_model=list[UserRewardOut])
def get_user_rewards(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_and_unlock_rewards(db, current_user)
    return db.query(UserReward).filter(UserReward.user_id == current_user.id).all()

@router.get("/points", response_model=UserPointsOut)
def get_user_points(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Example: You may want to calculate points from user activity
    available_points = current_user.flex_credit
    total_points = current_user.flex_credit  # Or sum of all earned points
    return UserPointsOut(available_points=available_points, total_points=total_points)

@router.post("/claim/{reward_id}")
def claim_reward(reward_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_reward = db.query(UserReward).filter_by(user_id=current_user.id, reward_id=reward_id).first()
    if not user_reward:
        raise HTTPException(status_code=404, detail="Reward not unlocked")
    if user_reward.claimed:
        raise HTTPException(status_code=400, detail="Reward already claimed")
    if user_reward.progress < user_reward.total:
        raise HTTPException(status_code=400, detail="Reward not yet unlocked")
    user_reward.claimed = 1
    db.commit()
    return {"message": "Reward claimed"}

def check_and_unlock_rewards(db: Session, user: User):
    rewards = db.query(Reward).all()
    for reward in rewards:
        user_reward = db.query(UserReward).filter_by(user_id=user.id, reward_id=reward.id).first()

        # "Regular Top-Up"
        if reward.name == "Regular Top-Up":
            payment_count = db.query(Payment).filter_by(user_id=user.id).count()
            if not user_reward:
                user_reward = UserReward(user_id=user.id, reward_id=reward.id, claimed=0, progress=payment_count, total=5)
                db.add(user_reward)
            else:
                user_reward.progress = payment_count
                user_reward.total = 5

        # "Gym Explorer"
        if reward.name == "Gym Explorer":
            unique_centers = db.query(CheckIn.center_id).filter_by(user_id=user.id).distinct().count()
            if not user_reward:
                user_reward = UserReward(user_id=user.id, reward_id=reward.id, claimed=0, progress=unique_centers, total=5)
                db.add(user_reward)
            else:
                user_reward.progress = unique_centers
                user_reward.total = 5

        # "Premium Member"
        if reward.name == "Premium Member":
            # Example: count months with active subscription (implement your own logic)
            months = getattr(user, "premium_months", 0)  # Replace with your real logic
            if not user_reward:
                user_reward = UserReward(user_id=user.id, reward_id=reward.id, claimed=0, progress=months, total=3)
                db.add(user_reward)
            else:
                user_reward.progress = months
                user_reward.total = 3

        # "Power User"
        if reward.name == "Power User":
            credits_used = getattr(user, "credits_used", 0)  # Replace with your real logic
            if not user_reward:
                user_reward = UserReward(user_id=user.id, reward_id=reward.id, claimed=0, progress=credits_used, total=500)
                db.add(user_reward)
            else:
                user_reward.progress = credits_used
                user_reward.total = 500

        # "Social Butterfly"
        if reward.name == "Social Butterfly":
            joined_activities, hosted_activities = get_activity_counts(db, user)
            if not user_reward:
                user_reward = UserReward(user_id=user.id, reward_id=reward.id, claimed=0, progress=joined_activities, total=5)
                db.add(user_reward)
            else:
                user_reward.progress = joined_activities
                user_reward.total = 5

        # "Community Leader"
        if reward.name == "Community Leader":
            joined_activities, hosted_activities = get_activity_counts(db, user)
            if not user_reward:
                user_reward = UserReward(user_id=user.id, reward_id=reward.id, claimed=0, progress=hosted_activities, total=3)
                db.add(user_reward)
            else:
                user_reward.progress = hosted_activities
                user_reward.total = 3

        # "Workout Buddy"
        if reward.name == "Workout Buddy":
            workouts_with_friends = db.query(Workout).filter_by(user_id=user.id, with_friends=True).count()
            if not user_reward:
                user_reward = UserReward(user_id=user.id, reward_id=reward.id, claimed=0, progress=workouts_with_friends, total=10)
                db.add(user_reward)
            else:
                user_reward.progress = workouts_with_friends
                user_reward.total = 10

        # "Early Bird"
        if reward.name == "Early Bird":
            early_workouts = count_early_workouts(db, user)
            if not user_reward:
                user_reward = UserReward(
                    user_id=user.id,
                    reward_id=reward.id,
                    claimed=0,
                    progress=early_workouts,
                    total=10
                )
                db.add(user_reward)
            else:
                user_reward.progress = early_workouts
                user_reward.total = 10

        # "Consistency King"
        if reward.name == "Consistency King":
            # Example: count workouts in current month
            from datetime import datetime
            now = datetime.now()
            month_workouts = db.query(Workout).filter(
                Workout.user_id == user.id,
                Workout.start_time >= datetime(now.year, now.month, 1)
            ).count()
            if not user_reward:
                user_reward = UserReward(user_id=user.id, reward_id=reward.id, claimed=0, progress=month_workouts, total=20)
                db.add(user_reward)
            else:
                user_reward.progress = month_workouts
                user_reward.total = 20

        # "Milestone Master"
        if reward.name == "Milestone Master":
            total_minutes = db.query(func.sum(Workout.duration_minutes)).filter_by(user_id=user.id).scalar() or 0
            if not user_reward:
                user_reward = UserReward(user_id=user.id, reward_id=reward.id, claimed=0, progress=total_minutes, total=1000)
                db.add(user_reward)
            else:
                user_reward.progress = total_minutes
                user_reward.total = 1000

        # "Variety Virtuoso"
        if reward.name == "Variety Virtuoso":
            workout_types = db.query(Workout.type).filter_by(user_id=user.id).distinct().count()
            if not user_reward:
                user_reward = UserReward(user_id=user.id, reward_id=reward.id, claimed=0, progress=workout_types, total=5)
                db.add(user_reward)
            else:
                user_reward.progress = workout_types
                user_reward.total = 5

        # "Challenge Champion"
        if reward.name == "Challenge Champion":
            challenges = db.query(MonthlyChallenge).filter_by(user_id=user.id, completed=True).count()
            if not user_reward:
                user_reward = UserReward(user_id=user.id, reward_id=reward.id, claimed=0, progress=challenges, total=3)
                db.add(user_reward)
            else:
                user_reward.progress = challenges
                user_reward.total = 3

        # Unlock if progress met
        if user_reward and user_reward.progress >= user_reward.total and not user_reward.claimed:
            user_reward.claimed = 0  # Unlocked but not claimed

    db.commit()

def get_activity_counts(db, user):
    joined_activities = db.query(GroupActivity).filter_by(user_id=user.id).count()
    hosted_activities = db.query(GroupActivity).filter_by(host_id=user.id).count()
    return joined_activities, hosted_activities

def count_early_workouts(db: Session, user):
    early_workouts = db.query(Workout).filter(
        Workout.user_id == user.id,
        extract('hour', Workout.start_time) < 8
    ).count()
    return early_workouts