from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    employee_ids: Optional[List[int]] = []

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    employee_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None

class Project(ProjectBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ProjectWithEmployees(Project):
    employees: List['Employee'] = []

# Import Employee here to avoid circular imports
from .employee import Employee
ProjectWithEmployees.model_rebuild()