from fastapi import APIRouter

from app.services.task_db_service import TaskDBService


router = APIRouter(tags=["tasks"])


@router.get("/tasks")
def list_tasks(limit: int = 50) -> dict:
    """列出最近分析任务。"""
    safe_limit = max(1, min(limit, 200))
    return {"items": TaskDBService.list_tasks(safe_limit)}
