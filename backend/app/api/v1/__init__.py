from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.repositories import router as repo_router
from app.api.v1.analyses import router as analysis_router
from app.api.v1.reports import router as report_router
from app.api.v1.dashboard import router as dashboard_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(repo_router, prefix="/repositories", tags=["repositories"])
api_router.include_router(analysis_router, prefix="/analyses", tags=["analyses"])
api_router.include_router(report_router, prefix="/reports", tags=["reports"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
