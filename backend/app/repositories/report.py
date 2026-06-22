from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report
from app.repositories.base import BaseRepository

class ReportRepository(BaseRepository[Report]):
    def __init__(self, db: AsyncSession):
        super().__init__(Report, db)

    async def get_by_analysis(self, analysis_id: UUID) -> Optional[Report]:
        result = await self.db.execute(select(Report).filter(Report.analysis_id == analysis_id))
        return result.scalars().first()
        
    async def get_by_repository(self, repository_id: UUID) -> Optional[Report]:
        from app.models.analysis import Analysis
        result = await self.db.execute(
            select(Report)
            .join(Analysis)
            .filter(Analysis.repository_id == repository_id, Analysis.status == "completed")
            .order_by(Analysis.completed_at.desc())
        )
        return result.scalars().first()
        
    async def search_reports(self, query: str, owner_id: UUID) -> list[Report]:
        # Simple search across repository name and report markdown contents
        from app.models.analysis import Analysis
        from app.models.repository import Repository
        result = await self.db.execute(
            select(Report)
            .join(Analysis)
            .join(Repository)
            .filter(
                Repository.owner_id == owner_id,
                (Repository.name.ilike(f"%{query}%") | Report.markdown_content.ilike(f"%{query}%"))
            )
            .order_by(Report.created_at.desc())
        )
        return list(result.scalars().all())
