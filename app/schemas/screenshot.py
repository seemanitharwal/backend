from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ScreenshotUpload(BaseModel):
    employee_id: int
    time_entry_id: Optional[int] = None
    permission_granted: bool = True
    device_info: Optional[str] = None

class Screenshot(BaseModel):
    id: int
    employee_id: int
    time_entry_id: Optional[int]
    filename: str
    file_path: str
    file_size: int
    timestamp: datetime
    permission_granted: bool
    width: Optional[int]
    height: Optional[int]
    format: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True