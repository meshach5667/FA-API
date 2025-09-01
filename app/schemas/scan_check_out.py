from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ScanCheckOutRequest(BaseModel):
    user_id: int
    center_id: int
    timestamp: str  # from QR code

class ScanCheckOutResponse(BaseModel):
    message: str

class ScanCheckOutHistoryOut(BaseModel):
    center_id: int
    center_name: str
    address: str
    state: str
    timestamp: datetime