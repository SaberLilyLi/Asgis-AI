from dataclasses import dataclass

from fastapi import HTTPException


@dataclass(frozen=True)
class ErrorDefinition:
    """标准错误定义，统一提供给 API 响应和任务失败状态使用。"""

    code: str
    message: str
    suggestion: str


ERROR_DEFINITIONS: dict[str, ErrorDefinition] = {
    "INVALID_GIT_URL": ErrorDefinition("INVALID_GIT_URL", "Git 仓库地址无效", "请使用 GitHub 或 Gitee 的 HTTPS 仓库地址。"),
    "REPO_CLONE_FAILED": ErrorDefinition("REPO_CLONE_FAILED", "仓库克隆失败", "请确认仓库存在、权限可访问且网络正常。"),
    "REPO_TOO_LARGE": ErrorDefinition("REPO_TOO_LARGE", "仓库体积超过限制", "请缩小仓库体积，或改用只包含前端工程的 zip 上传。"),
    "PRIVATE_REPO_DENIED": ErrorDefinition("PRIVATE_REPO_DENIED", "私有仓库无访问权限", "请填写有效的 GitHub/Gitee 访问 Token，或确认仓库为公开仓库。"),
    "ZIP_INVALID": ErrorDefinition("ZIP_INVALID", "ZIP 文件格式无效", "请重新压缩项目后上传，确保文件为标准 .zip 格式。"),
    "ZIP_TOO_LARGE": ErrorDefinition("ZIP_TOO_LARGE", "ZIP 文件超过大小限制", "请删除 node_modules、dist 等目录后重新上传。"),
    "SCAN_FAILED": ErrorDefinition("SCAN_FAILED", "项目扫描失败", "请确认项目目录结构正常，源码文件可读取。"),
    "NO_SUPPORTED_FILES": ErrorDefinition("NO_SUPPORTED_FILES", "未发现可分析的前端源码文件", "请确认项目包含 Vue、React、uni-app 或小程序源码。"),
    "ANALYZE_FAILED": ErrorDefinition("ANALYZE_FAILED", "工程规范分析失败", "请检查项目源码结构后重试。"),
    "RULE_GENERATE_FAILED": ErrorDefinition("RULE_GENERATE_FAILED", "规则生成失败", "请确认项目已分析成功后再生成规则。"),
    "PACKAGE_FAILED": ErrorDefinition("PACKAGE_FAILED", "规则包打包失败", "请稍后重试，或检查后端输出目录权限。"),
    "TASK_NOT_FOUND": ErrorDefinition("TASK_NOT_FOUND", "任务不存在", "请确认 task_id 是否正确，或重新创建分析任务。"),
    "UNKNOWN_ERROR": ErrorDefinition("UNKNOWN_ERROR", "未知错误", "请稍后重试，或查看后端日志定位原因。"),
}


def get_error(code: str, message: str | None = None, suggestion: str | None = None) -> ErrorDefinition:
    """按错误码获取标准错误，允许调用方覆盖 message 或 suggestion。"""
    base = ERROR_DEFINITIONS.get(code, ERROR_DEFINITIONS["UNKNOWN_ERROR"])
    return ErrorDefinition(code=base.code, message=message or base.message, suggestion=suggestion or base.suggestion)


def error_payload(code: str, message: str | None = None, suggestion: str | None = None) -> dict[str, str]:
    """生成标准错误响应体。"""
    error = get_error(code, message, suggestion)
    return {"code": error.code, "message": error.message, "suggestion": error.suggestion}


def raise_api_error(status_code: int, code: str, message: str | None = None, suggestion: str | None = None) -> None:
    """抛出统一格式的 HTTPException。"""
    raise HTTPException(status_code=status_code, detail=error_payload(code, message, suggestion))
