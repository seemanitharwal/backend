from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import create_access_token
from app.models.employee import Employee


class LoginRequest(BaseModel):
    email: EmailStr


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/login")
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Email-only login (desktop app). Accepts JSON: {"email": "user@example.com"}."""
    employee = (
        db.query(Employee)
        .filter(Employee.email == payload.email, Employee.is_verified == True)
        .first()
    )
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials or unverified user",
        )

    access_token = create_access_token({"sub": str(employee.id), "email": employee.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "employee": {"id": employee.id, "name": employee.name, "email": employee.email}
    } 