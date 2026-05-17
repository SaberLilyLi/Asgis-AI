import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.task_db_service import TaskDBService


class ProjectService:
    """项目存储服务，负责本地项目目录、分析结果和规则文件管理。"""

    BASE_DIR = Path(__file__).resolve().parents[2]
    STORAGE_DIR = BASE_DIR / "storage"
    PROJECTS_DIR = STORAGE_DIR / "projects"
    MAX_UPLOAD_BYTES = 80 * 1024 * 1024

    @classmethod
    def ensure_project_dirs(cls, project_id: str) -> None:
        """创建项目需要的 uploads、source、output 目录。"""
        cls.get_project_dir(project_id).mkdir(parents=True, exist_ok=True)
        cls.get_project_source_dir(project_id).mkdir(parents=True, exist_ok=True)
        cls.get_project_output_dir(project_id).mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_project_dir(cls, project_id: str) -> Path:
        """返回项目根存储目录。"""
        return cls.PROJECTS_DIR / project_id

    @classmethod
    def get_project_source_dir(cls, project_id: str) -> Path:
        """返回项目源码目录。"""
        return cls.get_project_dir(project_id) / "source"

    @classmethod
    def get_project_output_dir(cls, project_id: str) -> Path:
        """返回规则输出目录。"""
        return cls.get_project_dir(project_id) / "output"

    @classmethod
    def get_upload_zip_path(cls, project_id: str, filename: str) -> Path:
        """返回上传 zip 的保存路径。"""
        safe_name = Path(filename).name
        return cls.get_project_dir(project_id) / safe_name

    @classmethod
    def save_project_analysis(
        cls, project_id: str, source_type: str, source_path: str, analysis: dict[str, Any]
    ) -> None:
        """保存项目元数据与分析结果，供后续生成规则使用。"""
        payload = {
            "project_id": project_id,
            "source_type": source_type,
            "source_path": source_path,
            "analysis": analysis,
        }
        analysis_path = cls.get_project_dir(project_id) / "analysis.json"
        analysis_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        cls.update_project_status(
            project_id=project_id,
            status="success",
            stage="completed",
            progress=100,
            message="工程规范分析完成",
            analysis=analysis,
        )

    @classmethod
    def load_project(cls, project_id: str) -> dict[str, Any]:
        """读取项目分析结果。"""
        analysis_path = cls.get_project_dir(project_id) / "analysis.json"
        if not analysis_path.exists():
            raise FileNotFoundError(project_id)
        return json.loads(analysis_path.read_text(encoding="utf-8"))

    @classmethod
    def save_generated_rules(cls, project_id: str, generated: dict[str, str]) -> None:
        """将三类规则文件写入 output 目录。"""
        output_dir = cls.get_project_output_dir(project_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "rules.md").write_text(generated["rules_markdown"], encoding="utf-8")
        (output_dir / "development-flow.md").write_text(generated["development_flow"], encoding="utf-8")
        (output_dir / ".clinerules").write_text(generated["cline_rules"], encoding="utf-8")
        (output_dir / "cursor-rules.md").write_text(generated["cursor_rules"], encoding="utf-8")

    @classmethod
    def update_project_status(
        cls,
        project_id: str,
        status: str,
        stage: str,
        progress: int,
        message: str,
        code: str | None = None,
        suggestion: str | None = None,
        error: str | None = None,
        analysis: dict[str, Any] | None = None,
    ) -> None:
        """保存项目分析进度，供前端轮询展示。"""
        cls.ensure_project_dirs(project_id)
        current = cls.load_project_status(project_id, allow_missing=True)
        payload = {
            **current,
            "project_id": project_id,
            "status": status,
            "stage": stage,
            "progress": max(0, min(progress, 100)),
            "message": message,
            "code": code,
            "suggestion": suggestion,
            "error": error,
            "analysis": analysis if analysis is not None else current.get("analysis"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        status_path = cls.get_project_dir(project_id) / "status.json"
        status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        TaskDBService.update_task(
            project_id=project_id,
            status=status,
            stage=stage,
            progress=max(0, min(progress, 100)),
            message=message,
            code=code,
            suggestion=suggestion,
            error=error,
            analysis=payload.get("analysis"),
        )

    @classmethod
    def load_project_status(cls, project_id: str, allow_missing: bool = False) -> dict[str, Any]:
        """读取项目分析进度。"""
        status_path = cls.get_project_dir(project_id) / "status.json"
        if not status_path.exists():
            if allow_missing:
                return {}
            raise FileNotFoundError(project_id)
        return json.loads(status_path.read_text(encoding="utf-8"))
