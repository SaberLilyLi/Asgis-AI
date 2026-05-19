import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from app.models.task_model import now_iso


class TaskDBService:
    """SQLite 任务服务，用于持久化分析任务和状态历史。"""

    BASE_DIR = Path(__file__).resolve().parents[2]
    DB_PATH = BASE_DIR / "storage" / "asgis.db"

    @classmethod
    def init_db(cls) -> None:
        """初始化任务表。"""
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with cls._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_tasks (
                    project_id TEXT PRIMARY KEY,
                    source_type TEXT,
                    source_ref TEXT,
                    status TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    code TEXT,
                    message TEXT,
                    suggestion TEXT,
                    error TEXT,
                    tech_stack_json TEXT,
                    stats_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT
                )
                """
            )
            conn.commit()

    @classmethod
    def create_task(cls, project_id: str, source_type: str, source_ref: str) -> None:
        """创建任务记录。"""
        cls.init_db()
        now = cls._now()
        with cls._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO analysis_tasks (
                    project_id, source_type, source_ref, status, stage, progress,
                    code, message, suggestion, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    source_type,
                    source_ref,
                    "queued",
                    "uploading" if source_type == "zip" else "cloning",
                    5,
                    None,
                    "任务已创建",
                    None,
                    now,
                    now,
                ),
            )
            conn.commit()

    @classmethod
    def update_task(
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
        """更新任务状态。"""
        cls.init_db()
        tech_stack_json = None
        stats_json = None
        if analysis:
            tech_stack_json = json.dumps(analysis.get("tech_stack", {}), ensure_ascii=False)
            stats_json = json.dumps(analysis.get("stats", {}), ensure_ascii=False)
        completed_at = cls._now() if status in {"success", "failed"} else None
        with cls._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE analysis_tasks
                SET status = ?, stage = ?, progress = ?, code = ?, message = ?,
                    suggestion = ?, error = ?,
                    tech_stack_json = COALESCE(?, tech_stack_json),
                    stats_json = COALESCE(?, stats_json),
                    updated_at = ?, completed_at = COALESCE(?, completed_at)
                WHERE project_id = ?
                """,
                (
                    status,
                    stage,
                    progress,
                    code,
                    message,
                    suggestion,
                    error,
                    tech_stack_json,
                    stats_json,
                    cls._now(),
                    completed_at,
                    project_id,
                ),
            )
            if cursor.rowcount == 0:
                now = cls._now()
                conn.execute(
                    """
                    INSERT INTO analysis_tasks (
                        project_id, source_type, source_ref, status, stage, progress,
                        code, message, suggestion, error, tech_stack_json, stats_json,
                        created_at, updated_at, completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        "unknown",
                        "",
                        status,
                        stage,
                        progress,
                        code,
                        message,
                        suggestion,
                        error,
                        tech_stack_json,
                        stats_json,
                        now,
                        now,
                        completed_at,
                    ),
                )
            conn.commit()

    @classmethod
    def get_task(cls, project_id: str) -> dict[str, Any] | None:
        """读取单个任务。"""
        cls.init_db()
        with cls._connect() as conn:
            row = conn.execute("SELECT * FROM analysis_tasks WHERE project_id = ?", (project_id,)).fetchone()
            return cls._row_to_dict(row) if row else None

    @classmethod
    def list_tasks(cls, limit: int = 50) -> list[dict[str, Any]]:
        """列出最近任务。"""
        cls.init_db()
        with cls._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM analysis_tasks ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [cls._row_to_dict(row) for row in rows]

    @classmethod
    def list_cleanup_candidates(cls, cutoff_iso: str, keep_latest: int) -> list[dict[str, Any]]:
        """查询需要清理的任务，包含过期任务和超出保留数量的旧任务。"""
        cls.init_db()
        keep_latest = max(0, keep_latest)
        with cls._connect() as conn:
            expired_rows = conn.execute(
                """
                SELECT * FROM analysis_tasks
                WHERE status IN ('success', 'failed')
                  AND COALESCE(completed_at, updated_at, created_at) < ?
                ORDER BY created_at ASC
                """,
                (cutoff_iso,),
            ).fetchall()
            overflow_rows = conn.execute(
                """
                SELECT * FROM analysis_tasks
                WHERE project_id NOT IN (
                    SELECT project_id FROM analysis_tasks
                    ORDER BY created_at DESC
                    LIMIT ?
                )
                ORDER BY created_at ASC
                """,
                (keep_latest,),
            ).fetchall()

        candidates: dict[str, dict[str, Any]] = {}
        for row in [*expired_rows, *overflow_rows]:
            payload = cls._row_to_dict(row)
            candidates[payload["project_id"]] = payload
        return list(candidates.values())

    @classmethod
    def delete_tasks(cls, project_ids: list[str]) -> int:
        """批量删除任务数据库记录。"""
        if not project_ids:
            return 0
        cls.init_db()
        with cls._connect() as conn:
            cursor = conn.executemany(
                "DELETE FROM analysis_tasks WHERE project_id = ?",
                [(project_id,) for project_id in project_ids],
            )
            conn.commit()
        return cursor.rowcount if cursor.rowcount is not None else len(project_ids)

    @classmethod
    def _connect(cls) -> sqlite3.Connection:
        """创建 SQLite 连接。"""
        conn = sqlite3.connect(cls.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        """将 SQLite row 转成 dict。"""
        payload = dict(row)
        payload["tech_stack"] = json.loads(payload.pop("tech_stack_json") or "{}")
        payload["stats"] = json.loads(payload.pop("stats_json") or "{}")
        payload["task_id"] = payload["project_id"]
        payload["error_code"] = payload["code"] if payload.get("status") == "failed" else None
        payload["error_message"] = payload["error"] if payload.get("status") == "failed" else None
        return payload

    @staticmethod
    def _now() -> str:
        """返回 ISO 时间。"""
        return now_iso()
