import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.report import ReportResponse
from app.repositories.analysis import AnalysisRepository
from app.repositories.repository import RepositoryRepository
from app.repositories.report import ReportRepository

router = APIRouter()

@router.get("/analysis/{analysis_id}", response_model=ReportResponse)
async def get_report_by_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    analysis_repo = AnalysisRepository(db)
    report_repo = ReportRepository(db)
    repo_repo = RepositoryRepository(db)
    
    analysis = await analysis_repo.get(analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found."
        )
        
    repo = await repo_repo.get(analysis.repository_id)
    if not repo or (repo.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied."
        )
        
    report = await report_repo.get_by_analysis(analysis_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not generated yet or analysis failed."
        )
        
    return report

@router.get("/repository/{repository_id}", response_model=ReportResponse)
async def get_latest_report_by_repository(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo_repo = RepositoryRepository(db)
    report_repo = ReportRepository(db)
    
    repo = await repo_repo.get(repository_id)
    if not repo or repo.status == "deleted":
        raise HTTPException(status_code=404, detail="Repository not found")
        
    if repo.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=430, detail="Access denied")
        
    report = await report_repo.get_by_repository(repository_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reports found for this repository."
        )
        
    return report

@router.get("/search", response_model=list[ReportResponse])
async def search_reports(
    query: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report_repo = ReportRepository(db)
    return await report_repo.search_reports(query, current_user.id)

@router.get("/{report_id}/export")
async def export_report_markdown(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report_repo = ReportRepository(db)
    analysis_repo = AnalysisRepository(db)
    repo_repo = RepositoryRepository(db)
    
    report = await report_repo.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    analysis = await analysis_repo.get(report.analysis_id)
    repo = await repo_repo.get(analysis.repository_id)
    
    if repo.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
        
    # Return as standard file attachment
    filename = f"review_report_{repo.name}_{report_id}.md"
    return Response(
        content=report.markdown_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
