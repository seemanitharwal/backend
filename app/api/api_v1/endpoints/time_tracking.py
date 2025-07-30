from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, date, timezone
import logging

from app.core.database import get_db
from app.models.time_entry import TimeEntry
from app.models.employee import Employee
from app.models.project import Project
from app.models.task import Task
from app.schemas.time_entry import (
    TimeEntry as TimeEntrySchema,
    TimeEntryStart,
    TimeEntryStop,
    TimeEntryWithDetails
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/start", response_model=TimeEntrySchema, status_code=status.HTTP_201_CREATED)
async def start_time_tracking(time_data: TimeEntryStart, db: Session = Depends(get_db)):
    """Start a new time tracking session"""
    
    # Verify employee exists and is active
    employee = db.query(Employee).filter(
        Employee.id == time_data.employee_id,
        Employee.status == "active"
    ).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found or inactive"
        )
    
    # Verify project exists
    project = db.query(Project).filter(Project.id == time_data.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify task exists and belongs to project
    task = db.query(Task).filter(
        and_(Task.id == time_data.task_id, Task.project_id == time_data.project_id)
    ).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or doesn't belong to project"
        )
    
    # Check if employee has an active session
    active_session = db.query(TimeEntry).filter(
        and_(
            TimeEntry.employee_id == time_data.employee_id,
            TimeEntry.end_time.is_(None),
            TimeEntry.is_active == True
        )
    ).first()
    
    if active_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee already has an active time tracking session"
        )
    
    # Create new time entry
    time_entry = TimeEntry(
        employee_id=time_data.employee_id,
        project_id=time_data.project_id,
        task_id=time_data.task_id,
        start_time=datetime.now(timezone.utc),
        start_ip_address=time_data.ip_address,
        start_mac_address=time_data.mac_address,
        device_info=time_data.device_info
    )
    
    # Update employee device info
    employee.last_ip_address = time_data.ip_address
    employee.last_mac_address = time_data.mac_address
    employee.device_info = time_data.device_info
    
    db.add(time_entry)
    db.commit()
    db.refresh(time_entry)
    
    logger.info(f"Started time tracking for employee: {employee.email}, project: {project.name}")
    
    return time_entry

@router.post("/stop", response_model=TimeEntrySchema)
async def stop_time_tracking(stop_data: TimeEntryStop, db: Session = Depends(get_db)):
    """Stop the active time tracking session"""
    
    # Find active session for employee
    active_session = db.query(TimeEntry).filter(
        and_(
            TimeEntry.employee_id == stop_data.employee_id,
            TimeEntry.end_time.is_(None),
            TimeEntry.is_active == True
        )
    ).first()
    
    if not active_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active time tracking session found for employee"
        )
    
    # Update session with end time and calculate duration
    end_time = datetime.now(timezone.utc)
    active_session.end_time = end_time
    duration = (end_time - active_session.start_time).total_seconds()
    active_session.duration_seconds = int(duration)
    active_session.is_active = False
    
    db.commit()
    db.refresh(active_session)
    
    employee = db.query(Employee).filter(Employee.id == stop_data.employee_id).first()
    if employee:
        logger.info(f"Stopped time tracking for employee: {employee.email}, duration: {duration}s")
    else:
        logger.info(f"Stopped time tracking for employee_id {stop_data.employee_id}, duration: {duration}s")
    
    return active_session

@router.get("/employee/{employee_id}", response_model=List[TimeEntryWithDetails])
async def get_employee_time_entries(
    employee_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get time entries for a specific employee (for payout calculations)"""
    
    query = db.query(
        TimeEntry, Employee.name, Project.name, Task.name
    ).join(Employee).join(Project).join(Task).filter(
        TimeEntry.employee_id == employee_id
    )
    
    # Apply date filters
    if start_date:
        query = query.filter(TimeEntry.start_time >= start_date)
    
    if end_date:
        query = query.filter(TimeEntry.start_time <= end_date)
    
    # Order by start time descending
    query = query.order_by(TimeEntry.start_time.desc())
    
    time_entries = query.offset(skip).limit(limit).all()
    
    result = []
    for entry, emp_name, proj_name, task_name in time_entries:
        entry_dict = entry.__dict__.copy()
        entry_dict['employee_name'] = emp_name
        entry_dict['project_name'] = proj_name
        entry_dict['task_name'] = task_name
        result.append(TimeEntryWithDetails(**entry_dict))
    
    return result