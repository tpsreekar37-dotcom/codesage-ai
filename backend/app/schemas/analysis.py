from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class AnalysisBase(BaseModel):
    repository_id: UUID

class AnalysisCreate(AnalysisBase):
    pass

class AnalysisResponse(AnalysisBase):
    id: UUID
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_repositories: int
    total_analyses: int
    completed_analyses: int
    failed_analyses: int
    average_quality_score: float
    recent_analyses: List[AnalysisResponse]
