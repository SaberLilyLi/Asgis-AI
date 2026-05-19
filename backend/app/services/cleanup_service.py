import shutil
from datetime import datetime, timedelta

from app.config import settings
from app.services.project_service import ProjectService
from app.services.task_db_service import TaskDBService


class CleanupService:
    """任务清理服务，负责清理历史任务记录和对应项目文件。"""

    @classmethod
    def cleanup_tasks(cls, retention_days: int | None = None, max_count: int | None = None) -> dict:
        """按保留天数和最大数量清理任务，返回清理结果。"""
        days = retention_days if retention_days is not None else settings.TASK_RETENTION_DAYS
        keep_count = max_count if max_count is not None else settings.TASK_RETENTION_MAX_COUNT
        days = max(days, 1)
        keep_count = max(keep_count, 1)
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat(timespec="seconds")

        candidates = TaskDBService.list_cleanup_candidates(cutoff_iso, keep_count)
        deleted_projects: list[str] = []
        failed_projects: list[dict[str, str]] = []

        for task in candidates:
            project_id = task["project_id"]
            project_dir = ProjectService.get_project_dir(project_id)
            try:
                if project_dir.exists():
                    shutil.rmtree(project_dir)
                deleted_projects.append(project_id)
            except OSError as exc:
                failed_projects.append({"project_id": project_id, "reason": str(exc)})

        TaskDBService.delete_tasks(deleted_projects)
        return {
            "retention_days": days,
            "retention_max_count": keep_count,
            "deleted_count": len(deleted_projects),
            "deleted_project_ids": deleted_projects,
            "failed_count": len(failed_projects),
            "failed_projects": failed_projects,
        }
