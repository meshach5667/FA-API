from app.db.database import get_db
from app.models.reward import Reward
from app.models.workout import Workout
from sqlalchemy.orm import Session
from sqlalchemy import extract

def seed_rewards(db: Session):
    rewards = [
        Reward(
            name="Regular Top-Up",
            description="Top up your account 5 times",
            points_required=1000,
            category="payments",
            reward_type="credits",
            reward_value=50,
            reward_description="50 Flex Pass Credits"
        ),
        Reward(
            name="Gym Explorer",
            description="Visit 5 different fitness centers",
            points_required=1500,
            category="visits",
            reward_type="credits",
            reward_value=100,
            reward_description="100 Flex Pass Credits"
        ),
        Reward(
            name="Premium Member",
            description="Maintain subscription for 3 months",
            points_required=2000,
            category="payments",
            reward_type="discount",
            reward_value=15,
            reward_description="15% off next renewal"
        ),
        Reward(
            name="Power User",
            description="Use 500 flex pass credits",
            points_required=1200,
            category="visits",
            reward_type="credits",
            reward_value=75,
            reward_description="75 Bonus Credits"
        ),
        Reward(
            name="Social Butterfly",
            description="Join 5 group activities",
            points_required=800,
            category="social",
            reward_type="credits",
            reward_value=40,
            reward_description="40 Flex Pass Credits"
        ),
        Reward(
            name="Community Leader",
            description="Create and host 3 group activities",
            points_required=1500,
            category="social",
            reward_type="credits",
            reward_value=75,
            reward_description="75 Flex Pass Credits"
        ),
        Reward(
            name="Workout Buddy",
            description="Complete 10 workouts with friends",
            points_required=1000,
            category="social",
            reward_type="credits",
            reward_value=50,
            reward_description="50 Flex Pass Credits"
        ),
        Reward(
            name="Early Bird",
            description="Complete 10 workouts before 8 AM",
            points_required=1200,
            category="achievements",
            reward_type="credits",
            reward_value=60,
            reward_description="60 Flex Pass Credits"
        ),
        Reward(
            name="Consistency King",
            description="Work out 20 times in one month",
            points_required=2000,
            category="achievements",
            reward_type="credits",
            reward_value=100,
            reward_description="100 Flex Pass Credits"
        ),
        Reward(
            name="Milestone Master",
            description="Reach 1000 total workout minutes",
            points_required=1500,
            category="achievements",
            reward_type="credits",
            reward_value=75,
            reward_description="75 Flex Pass Credits + Achievement Badge"
        ),
        Reward(
            name="Variety Virtuoso",
            description="Try 5 different types of workouts",
            points_required=1000,
            category="achievements",
            reward_type="credits",
            reward_value=50,
            reward_description="50 Flex Pass Credits + Special Badge"
        ),
        Reward(
            name="Challenge Champion",
            description="Complete 3 monthly challenges",
            points_required=2500,
            category="achievements",
            reward_type="credits",
            reward_value=125,
            reward_description="125 Flex Pass Credits + Champion Badge"
        ),
    ]
    for reward in rewards:
        exists = db.query(Reward).filter_by(name=reward.name).first()
        if not exists:
            db.add(reward)
    db.commit()

