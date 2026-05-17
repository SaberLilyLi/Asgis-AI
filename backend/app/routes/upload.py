import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.services.analysis_task_service import AnalysisTaskService
from app.services.project_service import ProjectService
from app.services.task_db_service import TaskDBService


logger = logging.getLogger(__name__)
router = APIRouter(tags=["upload"])


@router.post("/upload_project")
async def upload_project(background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> dict:
    """上传 zip 项目并创建后台分析任务。"""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="仅支持上传 .zip 项目文件")

    project_id = str(uuid.uuid4())
    project_root = ProjectService.get_project_source_dir(project_id)
    zip_path = ProjectService.get_upload_zip_path(project_id, file.filename)

    try:
        ProjectService.ensure_project_dirs(project_id)
        content = await file.read()
        if len(content) > ProjectService.MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="上传文件过大，当前限制为 80MB")

        zip_path.write_bytes(content)
        TaskDBService.create_task(project_id, "zip", file.filename)
        ProjectService.update_project_status(project_id, "queued", "queued", 5, "项目已上传，等待开始分析")
        background_tasks.add_task(AnalysisTaskService.analyze_zip_project, project_id, zip_path, project_root)

        logger.info("zip 分析任务已创建 project_id=%s filename=%s", project_id, file.filename)
        return {
            "project_id": project_id,
            "status": "queued",
            "message": "项目已上传，正在排队分析",
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("上传项目任务创建失败")
        raise HTTPException(status_code=500, detail="上传项目任务创建失败") from exc
