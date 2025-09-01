from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
# from app.models.group_activity import GroupActivity

class Reward(Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    points_required = Column(Integer, nullable=False)
    category = Column(String, nullable=False)  # 'visits', 'payments', 'social', 'achievements'
    reward_type = Column(String, nullable=False)  # 'credits', 'discount', 'access'
    reward_value = Column(Float, nullable=False)
    reward_description = Column(String, nullable=False)

class UserReward(Base):
    __tablename__ = "user_rewards"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    reward_id = Column(Integer, ForeignKey("rewards.id"))
    claimed = Column(Integer, default=0)  # 0 = not claimed, 1 = claimed
    progress = Column(Integer, default=0)  # Track progress
    total = Column(Integer, default=1)     # Total needed to unlock

    reward = relationship("Reward")