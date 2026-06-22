import json
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.models.user import User
from app.models.repository import Repository
from app.models.analysis import Analysis
from app.models.report import Report
from app.schemas.analysis import DashboardStats, AnalysisResponse
from app.repositories.repository import RepositoryRepository
from app.repositories.analysis import AnalysisRepository

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    redis = get_redis_client()
    cache_key = f"user:dashboard_stats:{current_user.id}"
    
    # 1. Attempt to fetch from Redis
    if redis:
        try:
            cached_data = await redis.get(cache_key)
            if cached_data:
                stats_dict = json.loads(cached_data)
                return stats_dict
        except Exception:
            # Continue on Redis read error
            pass
            
    # 2. Database Aggregations
    # Total repositories
    repo_count_result = await db.execute(
        select(func.count(Repository.id))
        .filter(Repository.owner_id == current_user.id, Repository.status == "active")
    )
    total_repos = repo_count_result.scalar() or 0
    
    # Total analyses counts grouped by status
    status_counts_result = await db.execute(
        select(Analysis.status, func.count(Analysis.id))
        .join(Repository)
        .filter(Repository.owner_id == current_user.id)
        .group_by(Analysis.status)
    )
    status_counts = dict(status_counts_result.all())
    
    pending_count = status_counts.get("pending", 0)
    processing_count = status_counts.get("processing", 0)
    completed_count = status_counts.get("completed", 0)
    failed_count = status_counts.get("failed", 0)
    
    total_analyses = pending_count + processing_count + completed_count + failed_count
    
    # Average quality score of completed analyses
    avg_score_result = await db.execute(
        select(func.avg(Report.score_quality))
        .join(Analysis)
        .join(Repository)
        .filter(Repository.owner_id == current_user.id, Analysis.status == "completed")
    )
    avg_score = avg_score_result.scalar()
    avg_score = float(avg_score) if avg_score is not None else 100.0
    
    # 5 most recent analyses
    analysis_repo = AnalysisRepository(db)
    recent_analyses_models = await analysis_repo.get_latest_by_owner(current_user.id, limit=5)
    recent_analyses = [
        AnalysisResponse.model_validate(an) for an in recent_analyses_models
    ]
    
    # Assemble response
    stats_data = {
        "total_repositories": total_repos,
        "total_analyses": total_analyses,
        "completed_analyses": completed_count,
        "failed_analyses": failed_count,
        "average_quality_score": round(avg_score, 1),
        "recent_analyses": [an.model_dump() for an in recent_analyses]
    }
    
    # 3. Store in Redis with 60s TTL
    if redis:
        try:
            # We dump the schema using Pydantic dumps or json.dumps
            # To preserve UTC datetime fields, serialization to string is performed on dumped Pydantic models
            await redis.setex(cache_key, 60, json.dumps(stats_data, default=str))
        except Exception:
            pass
            
    return stats_data
