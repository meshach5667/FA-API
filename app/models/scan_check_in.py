from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class ScanCheckIn(Base):
    __tablename__ = "scan_check_ins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    center_id = Column(Integer, ForeignKey("centers.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # user = relationship("User")  # Commented out to avoid startup errors
    # center = relationship("Center")  # Commented out to avoid startup errors