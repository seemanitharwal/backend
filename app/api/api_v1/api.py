from fastapi import APIRouter
from app.api.api_v1.endpoints import employees, projects, tasks, time_tracking, screenshots, auth

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(time_tracking.router, prefix="/time-entries", tags=["time-tracking"])
api_router.include_router(screenshots.router, prefix="/screenshots", tags=["screenshots"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])