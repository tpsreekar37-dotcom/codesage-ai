from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID
from datetime import datetime
from typing import Optional

class RepositoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: str = Field(description="Must be 'zip' or 'github'")
    github_url: Optional[str] = None

class RepositoryCreate(RepositoryBase):
    pass

class RepositoryResponse(RepositoryBase):
    id: UUID
    status: str
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
class RepositoryDeleteResponse(BaseModel):
    message: str
    repository_id: UUID
