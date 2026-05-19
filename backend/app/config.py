import os
from pathlib import Path

from dotenv import load_dotenv


# 启动时读取 backend/.env，生产环境也可以直接使用系统环境变量覆盖。
BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


def get_int_env(name: str, default: int, minimum: int = 1) -> int:
    """读取整数环境变量，非法值自动回退默认配置。"""
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return max(value, minimum)


class Settings:
    """系统运行配置，集中管理上传、仓库和任务相关限制。"""

    MAX_UPLOAD_MB = get_int_env("ASGIS_MAX_UPLOAD_MB", 100)
    MAX_REPO_MB = get_int_env("ASGIS_MAX_REPO_MB", 200)
    CLONE_TIMEOUT_SECONDS = get_int_env("ASGIS_CLONE_TIMEOUT_SECONDS", 180)
    TASK_RETENTION_DAYS = get_int_env("ASGIS_TASK_RETENTION_DAYS", 7)
    TASK_RETENTION_MAX_COUNT = get_int_env("ASGIS_TASK_RETENTION_MAX_COUNT", 100)

    MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
    MAX_REPO_BYTES = MAX_REPO_MB * 1024 * 1024


settings = Settings()
