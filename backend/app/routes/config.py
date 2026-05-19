from fastapi import APIRouter

from app.config import settings


router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/limits")
def get_limits() -> dict:
    """返回当前后端限制配置，供前端展示和预校验使用。"""
    return {
        "max_upload_mb": settings.MAX_UPLOAD_MB,
        "max_repo_mb": settings.MAX_REPO_MB,
        "clone_timeout_seconds": settings.CLONE_TIMEOUT_SECONDS,
        "task_retention_days": settings.TASK_RETENTION_DAYS,
        "task_retention_max_count": settings.TASK_RETENTION_MAX_COUNT,
    }
