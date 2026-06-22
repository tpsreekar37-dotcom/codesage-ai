import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.repository import Repository
from app.models.audit import AuditLog
from app.schemas.repository import RepositoryResponse, RepositoryDeleteResponse
from app.repositories.repository import RepositoryRepository
from app.repositories.audit import AuditLogRepository
from app.services.repo_manager import RepoManagerService

router = APIRouter()

@router.post("/upload", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def upload_repository(
    request: Request,
    name: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo_repo = RepositoryRepository(db)
    audit_repo = AuditLogRepository(db)
    
    # 1. Validate file extension is .zip
    RepoManagerService.validate_zip_file(file)
    
    # 2. Extract ZIP safely
    local_path = RepoManagerService.process_zip_upload(file, current_user.id)
    
    # 3. Create Repository DB entry
    db_repo = Repository(
        name=name,
        type="zip",
        file_path=local_path,
        owner_id=current_user.id
    )
    repo = await repo_repo.create(db_repo)
    
    # 4. Audit Log
    audit = AuditLog(
        user_id=current_user.id,
        action="UPLOAD_REPO",
        details={"repository_id": str(repo.id), "name": repo.name},
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    await audit_repo.create(audit)
    
    return repo

@router.post("/clone", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def clone_repository(
    request: Request,
    name: str = Form(...),
    git_url: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo_repo = RepositoryRepository(db)
    audit_repo = AuditLogRepository(db)
    
    # 1. Clone Git repository safely
    local_path = RepoManagerService.clone_git_repository(git_url, current_user.id)
    
    # 2. Create Repository DB entry
    db_repo = Repository(
        name=name,
        type="github",
        github_url=git_url,
        file_path=local_path,
        owner_id=current_user.id
    )
    repo = await repo_repo.create(db_repo)
    
    # 3. Audit Log
    audit = AuditLog(
        user_id=current_user.id,
        action="CLONE_REPO",
        details={"repository_id": str(repo.id), "name": repo.name, "git_url": git_url},
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    await audit_repo.create(audit)
    
    return repo

@router.get("", response_model=List[RepositoryResponse])
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo_repo = RepositoryRepository(db)
    return await repo_repo.get_by_owner(current_user.id, skip=skip, limit=limit)

@router.delete("/{repository_id}", response_model=RepositoryDeleteResponse)
async def delete_repository(
    repository_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo_repo = RepositoryRepository(db)
    audit_repo = AuditLogRepository(db)
    
    repo = await repo_repo.get(repository_id)
    if not repo or repo.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found."
        )
        
    if repo.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this repository."
        )
        
    # Delete local files safely
    RepoManagerService.cleanup_repository_files(repo.file_path)
    
    # Soft delete repository in DB
    await repo_repo.update(repo, {"status": "deleted", "file_path": None})
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="DELETE_REPO",
        details={"repository_id": str(repo.id), "name": repo.name},
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    await audit_repo.create(audit)
    
    return {
        "message": "Repository successfully deleted",
        "repository_id": repository_id
    }
