from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.models.task import Task
from app.models.project import Project
from app.schemas.task import (
    Task as TaskSchema,
    TaskCreate,
    TaskUpdate
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task for a project"""
    
    # Verify project exists
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db_task = Task(
        name=task.name,
        description=task.description,
        project_id=task.project_id
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    logger.info(f"Created task: {db_task.name} for project: {project.name}")
    
    return db_task

@router.get("/", response_model=List[TaskSchema])
async def get_tasks(
    project_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of tasks, optionally filtered by project"""
    query = db.query(Task).filter(Task.is_active == True)
    
    if project_id:
        query = query.filter(Task.project_id == project_id)
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks

@router.get("/{task_id}", response_model=TaskSchema)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get task by ID"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task

@router.put("/{task_id}", response_model=TaskSchema)
async def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update task information"""
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Update fields
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    logger.info(f"Updated task: {task.name}")
    
    return task

@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def deactivate_task(task_id: int, db: Session = Depends(get_db)):
    """Soft delete/deactivate task"""
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    task.is_active = False
    db.commit()
    
    logger.info(f"Deactivated task: {task.name}")
    
    return {"message": "Task deactivated successfully"}