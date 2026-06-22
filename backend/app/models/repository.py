from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from app.core.database import Base

class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False) # "zip" or "github"
    github_url: Mapped[str] = mapped_column(String(1024), nullable=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=True) # local path on server where code is cloned/extracted
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False) # "active", "deleted"
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="repositories")
    analyses: Mapped[List["Analysis"]] = relationship(back_populates="repository", cascade="all, delete-orphan")
