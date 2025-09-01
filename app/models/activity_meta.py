from sqlalchemy import Column, Integer, ForeignKey, String, Text
from app.db.database import Base

class ActivityLike(Base):
    __tablename__ = "activity_likes"
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

class ActivityComment(Base):
    __tablename__ = "activity_comments"
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    comment = Column(Text, nullable=False)

class ActivityJoin(Base):
    __tablename__ = "activity_joins"
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    user_id = Column(Integer, ForeignKey("users.id"))