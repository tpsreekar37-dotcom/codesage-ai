from typing import Optional
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import UserSession
from app.repositories.base import BaseRepository

class UserSessionRepository(BaseRepository[UserSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(UserSession, db)

    async def get_by_token(self, refresh_token: str) -> Optional[UserSession]:
        result = await self.db.execute(
            select(UserSession).filter(UserSession.refresh_token == refresh_token, UserSession.is_revoked == False)
        )
        return result.scalars().first()

    async def revoke_all_by_user(self, user_id: UUID) -> None:
        await self.db.execute(
            update(UserSession)
            .filter(UserSession.user_id == user_id, UserSession.is_revoked == False)
            .values(is_revoked=True)
        )
        await self.db.commit()
        
    async def revoke_session(self, session_id: UUID) -> None:
        db_session = await self.get(session_id)
        if db_session:
            db_session.is_revoked = True
            await self.db.commit()
