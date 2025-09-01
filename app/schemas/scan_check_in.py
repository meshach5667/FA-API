from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ScanCheckInRequest(BaseModel):
    user_id: int
    center_id: int
    timestamp: str  # from QR code

class ScanCheckInResponse(BaseModel):
    message: str
    remaining_flex_credit: int

class ScanCheckInHistoryOut(BaseModel):
    center_id: int
    timestamp: datetime