from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class CheckInRequest(BaseModel):
    center_id: int

class QRCodeResponse(BaseModel):
    message: str
    qr_code_base64: str

class ScanConfirmRequest(BaseModel):
    user_id: int
    center_id: int
    timestamp: str

class CheckInHistoryCenterOut(BaseModel):
    center_id: int
    center_name: str
    address: str
    state: str
    timestamp: datetime

class CheckInHistoryFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None