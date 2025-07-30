from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.models.project import Project
from app.models.employee import Employee
from app.models.task import Task
from app.schemas.project import (
    Project as ProjectSchema,
    ProjectCreate,
    ProjectUpdate,
    ProjectWithEmployees
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project and automatically create a default task"""
    
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
    
    # Create default task for the project
    default_task = Task(
        name=f"Default Task - {project.name}",
        description="Default task created automatically for this project",
        project_id=db_project.id
    )
    
    db.add(default_task)
    db.commit()
    db.refresh(default_task)
    
    logger.info(f"Created project: {db_project.name} with ID: {db_project.id} and default task: {default_task.id}")
    
    return db_project

@router.get("/", response_model=List[ProjectWithEmployees])
async def get_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of all active projects with assigned employees"""
    projects = db.query(Project).filter(Project.is_active == True).offset(skip).limit(limit).all()
    return projects

@router.patch("/{project_id}", response_model=ProjectWithEmployees)
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
async def delete_project(project_id: int, db: Session = Depends(get_db)):
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

@router.post("/{project_id}/tasks/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_project_task(project_id: int, task_data: dict, db: Session = Depends(get_db)):
    """Create a task for a specific project"""
    
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    task = Task(
        name=task_data.get("name", f"Task for {project.name}"),
        description=task_data.get("description", ""),
        project_id=project_id
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    logger.info(f"Created task: {task.name} for project: {project.name}")
    
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "project_id": task.project_id,
        "created_at": task.created_at
    }