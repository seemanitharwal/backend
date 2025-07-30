from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.models.project import Project
from app.models.employee import Employee
from app.schemas.project import (
    Project as ProjectSchema,
    ProjectCreate,
    ProjectUpdate,
    ProjectWithEmployees
)
from app.schemas.employee import Employee as EmployeeSchema

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    
    db_project = Project(
        name=project.name,
        description=project.description
    )
    
    # Add employees to project if provided
    if project.employee_ids:
        employees = db.query(Employee).filter(Employee.id.in_(project.employee_ids)).all()
        db_project.employees = employees
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    logger.info(f"Created project: {db_project.name} with ID: {db_project.id}")
    
    return db_project

@router.get("/", response_model=List[ProjectWithEmployees])
async def get_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of all active projects with assigned employees"""
    projects = db.query(Project).filter(Project.is_active == True).offset(skip).limit(limit).all()
    return projects

@router.get("/{project_id}", response_model=ProjectWithEmployees)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get project by ID with assigned employees"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project

@router.get("/{project_id}/employees", response_model=List[EmployeeSchema])
async def get_project_employees(project_id: int, db: Session = Depends(get_db)):
    """Get employees assigned to a specific project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project.employees

@router.put("/{project_id}", response_model=ProjectWithEmployees)
async def update_project(project_id: int, project_update: ProjectUpdate, db: Session = Depends(get_db)):
    """Update project details and employee assignments"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update basic fields
    update_data = project_update.dict(exclude_unset=True, exclude={'employee_ids'})
    for field, value in update_data.items():
        setattr(project, field, value)
    
    # Update employee assignments if provided
    if project_update.employee_ids is not None:
        employees = db.query(Employee).filter(Employee.id.in_(project_update.employee_ids)).all()
        project.employees = employees
    
    db.commit()
    db.refresh(project)
    
    logger.info(f"Updated project: {project.name}")
    
    return project

@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
async def deactivate_project(project_id: int, db: Session = Depends(get_db)):
    """Soft delete/deactivate project"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project.is_active = False
    db.commit()
    
    logger.info(f"Deactivated project: {project.name}")
    
    return {"message": "Project deactivated successfully"}