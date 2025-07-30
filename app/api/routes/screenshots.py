from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import os
import uuid
import logging
from PIL import Image
import json

from app.core.database import get_db
from app.core.config import settings
from app.models.screenshot import Screenshot
from app.models.employee import Employee
from app.models.time_entry import TimeEntry
from app.schemas.screenshot import (
    Screenshot as ScreenshotSchema,
    ScreenshotUpload
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)

@router.post("/", response_model=ScreenshotSchema, status_code=status.HTTP_201_CREATED)
async def upload_screenshot(
    file: UploadFile = File(...),
    employee_id: int = Form(...),
    time_entry_id: Optional[int] = Form(None),
    permission_granted: bool = Form(True),
    device_info: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a screenshot"""
    
    # Verify employee exists
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Verify time entry if provided
    if time_entry_id:
        time_entry = db.query(TimeEntry).filter(
            TimeEntry.id == time_entry_id,
            TimeEntry.employee_id == employee_id
        ).first()
        if not time_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found or doesn't belong to employee"
            )
    
    # Validate file
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > settings.max_screenshot_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.max_screenshot_size} bytes"
        )
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in settings.allowed_screenshot_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File format not allowed. Allowed formats: {settings.allowed_screenshot_formats}"
        )
    
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    
    try:
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Process image to get metadata
        with Image.open(file_path) as img:
            width, height = img.size
            img_format = img.format
            
            # Compress image if needed
            if img.format in ['JPEG', 'JPG']:
                img.save(
                    file_path, 
                    format='JPEG', 
                    quality=settings.screenshot_compression_quality,
                    optimize=True
                )
        
        # Get final file size after compression
        final_file_size = os.path.getsize(file_path)
        
        # Create screenshot record
        screenshot = Screenshot(
            employee_id=employee_id,
            time_entry_id=time_entry_id,
            filename=unique_filename,
            file_path=file_path,
            file_size=final_file_size,
            timestamp=datetime.utcnow(),
            permission_granted=permission_granted,
            width=width,
            height=height,
            format=img_format,
            device_info=device_info
        )
        
        db.add(screenshot)
        db.commit()
        db.refresh(screenshot)
        
        logger.info(f"Screenshot uploaded for employee: {employee.email}, file: {unique_filename}")
        
        return screenshot
        
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Error uploading screenshot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing screenshot"
        )

@router.get("/", response_model=List[ScreenshotSchema])
async def get_screenshots(
    employee_id: Optional[int] = None,
    time_entry_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    permission_granted: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get screenshots with filtering options"""
    
    query = db.query(Screenshot)
    
    # Apply filters
    if employee_id:
        query = query.filter(Screenshot.employee_id == employee_id)
    
    if time_entry_id:
        query = query.filter(Screenshot.time_entry_id == time_entry_id)
    
    if start_date:
        query = query.filter(Screenshot.timestamp >= start_date)
    
    if end_date:
        query = query.filter(Screenshot.timestamp <= end_date)
    
    if permission_granted is not None:
        query = query.filter(Screenshot.permission_granted == permission_granted)
    
    # Order by timestamp descending
    query = query.order_by(Screenshot.timestamp.desc())
    
    screenshots = query.offset(skip).limit(limit).all()
    return screenshots

@router.get("/{screenshot_id}", response_model=ScreenshotSchema)
async def get_screenshot(screenshot_id: int, db: Session = Depends(get_db)):
    """Get screenshot metadata by ID"""
    
    screenshot = db.query(Screenshot).filter(Screenshot.id == screenshot_id).first()
    if not screenshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screenshot not found"
        )
    
    return screenshot

@router.get("/{screenshot_id}/download")
async def download_screenshot(screenshot_id: int, db: Session = Depends(get_db)):
    """Download screenshot file"""
    
    screenshot = db.query(Screenshot).filter(Screenshot.id == screenshot_id).first()
    if not screenshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screenshot not found"
        )
    
    if not os.path.exists(screenshot.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screenshot file not found on disk"
        )
    
    return FileResponse(
        screenshot.file_path,
        filename=screenshot.filename,
        media_type='image/' + screenshot.format.lower()
    )

@router.delete("/{screenshot_id}", status_code=status.HTTP_200_OK)
async def delete_screenshot(screenshot_id: int, db: Session = Depends(get_db)):
    """Delete screenshot and its file"""
    
    screenshot = db.query(Screenshot).filter(Screenshot.id == screenshot_id).first()
    if not screenshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screenshot not found"
        )
    
    # Delete file from disk
    if os.path.exists(screenshot.file_path):
        try:
            os.remove(screenshot.file_path)
        except Exception as e:
            logger.error(f"Error deleting screenshot file: {str(e)}")
    
    # Delete from database
    db.delete(screenshot)
    db.commit()
    
    logger.info(f"Deleted screenshot: {screenshot.filename}")
    
    return {"message": "Screenshot deleted successfully"}