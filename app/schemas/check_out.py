from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class CheckOutRequest(BaseModel):
    center_id: int

class CheckOutQRCodeResponse(BaseModel):
    message: str
    qr_code_base64: str

class CheckOutScanConfirmRequest(BaseModel):
    user_id: int
    center_id: int
    timestamp: str

class CheckOutHistoryCenterOut(BaseModel):
    center_id: int
    center_name: str
    address: str
    state: str
    timestamp: datetime