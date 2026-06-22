from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.analysis import Analysis
from app.repositories.base import BaseRepository

class AnalysisRepository(BaseRepository[Analysis]):
    def __init__(self, db: AsyncSession):
        super().__init__(Analysis, db)

    async def get_by_repository(self, repository_id: UUID, skip: int = 0, limit: int = 100) -> List[Analysis]:
        result = await self.db.execute(
            select(Analysis)
            .filter(Analysis.repository_id == repository_id)
            .order_by(Analysis.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_report(self, analysis_id: UUID) -> Optional[Analysis]:
        result = await self.db.execute(
            select(Analysis)
            .filter(Analysis.id == analysis_id)
            .options(selectinload(Analysis.report))
        )
        return result.scalars().first()

    async def get_latest_by_owner(self, owner_id: UUID, limit: int = 5) -> List[Analysis]:
        from app.models.repository import Repository
        result = await self.db.execute(
            select(Analysis)
            .join(Repository)
            .filter(Repository.owner_id == owner_id)
            .order_by(Analysis.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
