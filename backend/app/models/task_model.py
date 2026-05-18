from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TaskStatus = Literal["queued", "running", "success", "failed"]
TaskStage = Literal["uploading", "cloning", "scanning", "analyzing", "generating", "packaging", "done", "error"]


class TaskInfo(BaseModel):
    """统一任务状态模型，后续接口和数据库迁移都以该结构为准。"""

    task_id: str
    status: TaskStatus
    stage: TaskStage
    progress: int = Field(ge=0, le=100)
    message: str
    error_code: str | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str


def now_iso() -> str:
    """返回秒级 ISO 时间字符串。"""
    return datetime.now().isoformat(timespec="seconds")
