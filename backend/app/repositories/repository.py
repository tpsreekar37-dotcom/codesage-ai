from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.repository import Repository
from app.repositories.base import BaseRepository

class RepositoryRepository(BaseRepository[Repository]):
    def __init__(self, db: AsyncSession):
        super().__init__(Repository, db)

    async def get_by_owner(self, owner_id: UUID, skip: int = 0, limit: int = 100) -> List[Repository]:
        result = await self.db.execute(
            select(Repository)
            .filter(Repository.owner_id == owner_id, Repository.status == "active")
            .order_by(Repository.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_count_by_owner(self, owner_id: UUID) -> int:
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count())
            .select_from(Repository)
            .filter(Repository.owner_id == owner_id, Repository.status == "active")
        )
        return result.scalar() or 0
