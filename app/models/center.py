from sqlalchemy import Column, Integer, String, Float, JSON
from app.db.database import Base

class Center(Base):
    __tablename__ = "centers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    address = Column(String)
    state = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    center_type = Column(String)
    credit_required = Column(Integer, default=1)  # Flex credit required for entry
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    comments = Column(JSON, default=[])