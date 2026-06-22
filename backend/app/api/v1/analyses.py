import uuid
import datetime
import logging
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db, async_session_maker
from app.models.user import User
from app.models.analysis import Analysis
from app.models.report import Report
from app.models.audit import AuditLog
from app.schemas.analysis import AnalysisResponse, AnalysisCreate
from app.repositories.repository import RepositoryRepository
from app.repositories.analysis import AnalysisRepository
from app.repositories.report import ReportRepository
from app.repositories.audit import AuditLogRepository
from app.services.ai_engine import AIEngineService

router = APIRouter()
logger = logging.getLogger("app.analyses")

async def run_ai_analysis_task(analysis_id: uuid.UUID, file_path: str):
    """Background task to run code review and update db records."""
    # We open a new database session because background tasks execute outside the request lifecycle
    async with async_session_maker() as db:
        analysis_repo = AnalysisRepository(db)
        report_repo = ReportRepository(db)
        
        analysis = await analysis_repo.get(analysis_id)
        if not analysis:
            logger.error(f"Analysis with ID {analysis_id} not found in background task.")
            return
            
        # 1. Update status to processing
        analysis.status = "processing"
        await db.commit()
        
        try:
            # 2. Invoke Gemini analysis
            review_result = await AIEngineService.analyze_codebase(file_path)
            
            # 3. Create Report model
            report = Report(
                analysis_id=analysis_id,
                score_quality=review_result["score_quality"],
                score_security=review_result["score_security"],
                score_performance=review_result["score_performance"],
                score_maintainability=review_result["score_maintainability"],
                findings=review_result["findings"],
                markdown_content=review_result["markdown_report"]
            )
            await report_repo.create(report)
            
            # 4. Mark analysis as completed
            analysis.status = "completed"
            analysis.completed_at = datetime.datetime.utcnow()
            await db.commit()
            logger.info(f"AI review completed successfully for Analysis {analysis_id}.")
            
        except Exception as e:
            logger.error(f"Error executing AI analysis for Analysis {analysis_id}: {str(e)}")
            analysis.status = "failed"
            analysis.error_message = str(e)
            analysis.completed_at = datetime.datetime.utcnow()
            await db.commit()

@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    analysis_in: AnalysisCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo_repo = RepositoryRepository(db)
    analysis_repo = AnalysisRepository(db)
    audit_repo = AuditLogRepository(db)
    
    # Verify repository ownership
    repo = await repo_repo.get(analysis_in.repository_id)
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
        
    if not repo.file_path or not os.path.exists(repo.file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository files are missing or deleted."
        )
        
    # Create Analysis record
    db_analysis = Analysis(
        repository_id=repo.id,
        status="pending"
    )
    analysis = await analysis_repo.create(db_analysis)
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="START_ANALYSIS",
        details={"repository_id": str(repo.id), "analysis_id": str(analysis.id)},
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    await audit_repo.create(audit)
    
    # Queue background task execution
    background_tasks.add_task(run_ai_analysis_task, analysis.id, repo.file_path)
    
    return analysis

@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_status(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    analysis_repo = AnalysisRepository(db)
    analysis = await analysis_repo.get(analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found."
        )
        
    # Owner permission check
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get(analysis.repository_id)
    if not repo or (repo.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied."
        )
        
    return analysis

@router.get("/repo/{repository_id}", response_model=List[AnalysisResponse])
async def list_repo_analyses(
    repository_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get(repository_id)
    if not repo or repo.status == "deleted":
        raise HTTPException(status_code=404, detail="Repository not found")
        
    if repo.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
        
    analysis_repo = AnalysisRepository(db)
    return await analysis_repo.get_by_repository(repository_id, skip=skip, limit=limit)
