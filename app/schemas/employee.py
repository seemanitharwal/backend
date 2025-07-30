from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class EmployeeBase(BaseModel):
    name: str
    email: EmailStr

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[str] = None

class EmployeeVerify(BaseModel):
    token: str

class Employee(EmployeeBase):
    id: int
    status: str
    is_verified: bool
    last_mac_address: Optional[str]
    last_ip_address: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class EmployeeWithToken(Employee):
    verification_token: Optional[str]