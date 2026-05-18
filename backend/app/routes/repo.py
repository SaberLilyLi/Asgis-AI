import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.models.error_model import raise_api_error
from app.models.rule_model import RepoAnalyzeRequest
from app.services.analysis_task_service import AnalysisTaskService
from app.services.project_service import ProjectService
from app.services.repo_service import RepoService
from app.services.task_db_service import TaskDBService


logger = logging.getLogger(__name__)
router = APIRouter(tags=["repo"])


@router.post("/analyze_repo")
def analyze_repo(payload: RepoAnalyzeRequest, background_tasks: BackgroundTasks) -> dict:
    """创建 GitHub / Gitee 仓库后台分析任务，Token 仅在本次任务内存中使用。"""
    try:
        RepoService.validate_repo_url(payload.git_url)
    except ValueError as exc:
        raise_api_error(400, "INVALID_GIT_URL", str(exc), "请使用 GitHub / Gitee 的 HTTPS 仓库地址。")

    project_id = str(uuid.uuid4())
    repo_dir = ProjectService.get_project_source_dir(project_id)

    try:
        ProjectService.ensure_project_dirs(project_id)
        TaskDBService.create_task(project_id, "git", payload.git_url)
        ProjectService.update_project_status(
            project_id,
            "queued",
            "cloning",
            5,
            "仓库分析任务已创建",
            suggestion="请等待后台任务开始克隆仓库。",
        )
        background_tasks.add_task(
            AnalysisTaskService.analyze_repo_project,
            project_id,
            payload.git_url,
            repo_dir,
            payload.access_token,
        )

        logger.info("仓库分析任务已创建 project_id=%s url=%s token=%s", project_id, payload.git_url, bool(payload.access_token))
        return {
            "project_id": project_id,
            "status": "queued",
            "message": "仓库分析任务已创建，正在排队分析",
            "code": "TASK_QUEUED",
        }
    except Exception as exc:
        logger.exception("仓库分析任务创建失败")
        raise_api_error(500, "UNKNOWN_ERROR", "仓库分析任务创建失败", "请稍后重试，或检查后端服务日志。")
