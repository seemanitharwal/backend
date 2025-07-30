from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TimeEntryStart(BaseModel):
    employee_id: int
    project_id: int
    task_id: int
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    device_info: Optional[str] = None

class TimeEntryStop(BaseModel):
    employee_id: int

class TimeEntry(BaseModel):
    id: int
    employee_id: int
    project_id: int
    task_id: int
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    start_ip_address: Optional[str]
    start_mac_address: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TimeEntryWithDetails(TimeEntry):
    employee_name: Optional[str]
    project_name: Optional[str]
    task_name: Optional[str]