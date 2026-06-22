from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class FindingItemSchema(BaseModel):
    severity: str
    file: str
    line: Optional[int] = None
    category: str
    message: str
    suggestion: str

class ReportResponse(BaseModel):
    id: UUID
    analysis_id: UUID
    score_quality: int
    score_security: int
    score_performance: int
    score_maintainability: int
    findings: List[FindingItemSchema]
    markdown_content: str
    created_at: datetime

    class Config:
        from_attributes = True
