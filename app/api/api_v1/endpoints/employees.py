from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.core.security import create_verification_token, verify_verification_token
from app.core.email_utils import send_verification_email
from app.core.config import settings
from app.models.employee import Employee
from app.schemas.employee import (
    Employee as EmployeeSchema, 
    EmployeeCreate, 
    EmployeeUpdate, 
    EmployeeVerify,
    EmployeeWithToken
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=EmployeeWithToken, status_code=status.HTTP_201_CREATED)
async def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    """Create a new employee with verification token"""
    
    # Check if employee already exists
    existing_employee = db.query(Employee).filter(Employee.email == employee.email).first()
    if existing_employee:
        if existing_employee.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee with this email already exists and is verified"
            )

        verification_token = create_verification_token(existing_employee.id)
        existing_employee.verification_token = verification_token
        db.commit()
        db.refresh(existing_employee)

        verification_link = f"{settings.frontend_url}/verify-email?token={verification_token}&id={existing_employee.id}"
        send_verification_email(existing_employee.email, verification_link)

        return existing_employee
    
    # Create new employee
    db_employee = Employee(
        name=employee.name,
        email=employee.email,
        status="inactive",  # Will be activated on verification
        is_verified=False
    )
    
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    
    # Generate verification token
    verification_token = create_verification_token(db_employee.id)
    db_employee.verification_token = verification_token
    db.commit()
    db.refresh(db_employee)

    # Construct verification link
    base_url = settings.frontend_url
    verification_link = f"{base_url}/verify-email?token={verification_token}&id={db_employee.id}"
    send_verification_email(db_employee.email, verification_link)
    
    logger.info(f"Created employee: {db_employee.email} with ID: {db_employee.id}")
    
    return db_employee

@router.get("/", response_model=List[EmployeeSchema])
async def get_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of all employees"""
    employees = db.query(Employee).offset(skip).limit(limit).all()
    return employees

@router.get("/{employee_id}", response_model=EmployeeSchema)
async def get_employee(employee_id: int, db: Session = Depends(get_db)):
    """Get employee by ID"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    return employee

@router.patch("/{employee_id}", response_model=EmployeeSchema)
async def update_employee(employee_id: int, employee_update: EmployeeUpdate, db: Session = Depends(get_db)):
    """Update employee information"""
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Update fields
    update_data = employee_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)
    
    db.commit()
    db.refresh(employee)
    
    logger.info(f"Updated employee: {employee.email}")
    
    return employee

@router.delete("/{employee_id}", status_code=status.HTTP_200_OK)
async def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    """Soft delete/deactivate employee"""
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    employee.status = "inactive"
    db.commit()
    
    logger.info(f"Deactivated employee: {employee.email}")
    
    return {"message": "Employee deactivated successfully"}

@router.post("/{employee_id}/verify", response_model=EmployeeSchema)
async def verify_employee(employee_id: int, verify_data: EmployeeVerify, db: Session = Depends(get_db)):
    """Verify employee using verification token"""
    
    # Verify token
    token_employee_id = verify_verification_token(verify_data.token)
    if not token_employee_id or token_employee_id != employee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Get employee
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Update employee status
    employee.is_verified = True
    employee.status = "active"
    employee.verification_token = None  # Clear token after use
    
    db.commit()
    db.refresh(employee)
    
    logger.info(f"Verified employee: {employee.email}")
    
    return employee