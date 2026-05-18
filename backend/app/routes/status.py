from fastapi import APIRouter, HTTPException

from app.models.error_model import raise_api_error
from app.services.project_service import ProjectService


router = APIRouter(tags=["status"])


@router.get("/project_status/{project_id}")
def get_project_status(project_id: str) -> dict:
    """查询项目分析任务状态，供前端轮询进度。"""
    try:
        return ProjectService.load_project_status(project_id)
    except FileNotFoundError as exc:
        raise_api_error(404, "TASK_NOT_FOUND")
