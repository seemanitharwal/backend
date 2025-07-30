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

@router.patch("/{task_id}", response_model=TaskSchema)
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
async def delete_task(task_id: int, db: Session = Depends(get_db)):
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