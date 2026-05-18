import logging
import uuid
import zipfile
from io import BytesIO

from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from fastapi.responses import StreamingResponse

from app.models.error_model import raise_api_error
from app.models.rule_model import RepoAnalyzeRequest
from app.services.analysis_task_service import AnalysisTaskService
from app.services.project_service import ProjectService
from app.services.repo_service import RepoService
from app.services.rules_generator_service import RulesGeneratorService
from app.services.task_db_service import TaskDBService


logger = logging.getLogger(__name__)
router = APIRouter(tags=["tasks"])


@router.get("/tasks")
def list_tasks(limit: int = 50) -> dict:
    """列出最近分析任务，保留旧接口兼容当前前端。"""
    safe_limit = max(1, min(limit, 200))
    return {"items": TaskDBService.list_tasks(safe_limit)}


@router.post("/api/tasks/upload")
async def create_upload_task(background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> dict:
    """上传 ZIP 并创建分析任务。"""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise_api_error(400, "ZIP_INVALID", "仅支持上传 .zip 项目文件", "请选择标准 .zip 项目压缩包后重新上传。")

    task_id = str(uuid.uuid4())
    project_root = ProjectService.get_project_source_dir(task_id)
    zip_path = ProjectService.get_upload_zip_path(task_id, file.filename)

    try:
        ProjectService.ensure_project_dirs(task_id)
        content = await file.read()
        if len(content) > ProjectService.MAX_UPLOAD_BYTES:
            raise_api_error(413, "ZIP_TOO_LARGE", "上传文件过大，当前限制为 80MB", "请删除 node_modules、dist 等目录后重新压缩上传。")

        zip_path.write_bytes(content)
        TaskDBService.create_task(task_id, "zip", file.filename)
        ProjectService.update_project_status(task_id, "queued", "uploading", 5, "项目已上传，等待开始分析")
        background_tasks.add_task(AnalysisTaskService.analyze_zip_project, task_id, zip_path, project_root)

        logger.info("统一任务接口创建 zip 分析任务 task_id=%s filename=%s", task_id, file.filename)
        return {"task_id": task_id}
    except Exception as exc:
        if exc.__class__.__name__ == "HTTPException":
            raise
        logger.exception("创建 ZIP 分析任务失败")
        raise_api_error(500, "UNKNOWN_ERROR", "创建 ZIP 分析任务失败", "请稍后重试，或查看后端日志定位原因。")


@router.post("/api/tasks/git")
def create_git_task(payload: RepoAnalyzeRequest, background_tasks: BackgroundTasks) -> dict:
    """提交 Git 仓库地址并创建分析任务。"""
    try:
        RepoService.validate_repo_url(payload.git_url)
    except ValueError as exc:
        raise_api_error(400, "INVALID_GIT_URL", str(exc), "请使用 GitHub / Gitee 的 HTTPS 仓库地址。")

    task_id = str(uuid.uuid4())
    repo_dir = ProjectService.get_project_source_dir(task_id)

    try:
        ProjectService.ensure_project_dirs(task_id)
        TaskDBService.create_task(task_id, "git", payload.git_url)
        ProjectService.update_project_status(task_id, "queued", "cloning", 5, "仓库分析任务已创建")
        background_tasks.add_task(
            AnalysisTaskService.analyze_repo_project,
            task_id,
            payload.git_url,
            repo_dir,
            payload.access_token,
        )

        logger.info("统一任务接口创建 Git 分析任务 task_id=%s url=%s token=%s", task_id, payload.git_url, bool(payload.access_token))
        return {"task_id": task_id}
    except Exception as exc:
        if exc.__class__.__name__ == "HTTPException":
            raise
        logger.exception("创建 Git 分析任务失败")
        raise_api_error(500, "UNKNOWN_ERROR", "创建 Git 分析任务失败", "请稍后重试，或检查后端服务日志。")


@router.get("/api/tasks/{task_id}")
def get_task_status(task_id: str) -> dict:
    """查询任务状态。"""
    try:
        status = ProjectService.load_project_status(task_id)
    except FileNotFoundError:
        raise_api_error(404, "TASK_NOT_FOUND")
    return _task_status_payload(status)


@router.get("/api/tasks/{task_id}/result")
def get_task_result(task_id: str) -> dict:
    """查询任务分析结果。"""
    status = _load_status_or_404(task_id)
    if status.get("status") == "failed":
        raise_api_error(
            409,
            status.get("error_code") or "ANALYZE_FAILED",
            status.get("error_message") or status.get("message") or "任务分析失败",
            status.get("suggestion") or "请修复失败原因后重新创建分析任务。",
        )
    if status.get("status") != "success":
        raise_api_error(409, "ANALYZE_FAILED", "任务尚未完成，暂时无法获取分析结果", "请等待任务状态变为 success 后再查询结果。")

    try:
        project = ProjectService.load_project(task_id)
    except FileNotFoundError:
        raise_api_error(404, "TASK_NOT_FOUND")

    return _build_task_result(task_id, project)


@router.get("/api/tasks/{task_id}/download")
def download_task_rules(task_id: str) -> StreamingResponse:
    """下载完整规则包。"""
    status = _load_status_or_404(task_id)
    if status.get("status") == "failed":
        raise_api_error(
            409,
            status.get("error_code") or "ANALYZE_FAILED",
            status.get("error_message") or status.get("message") or "任务分析失败，无法下载规则包",
            status.get("suggestion") or "请修复失败原因后重新创建分析任务。",
        )
    if status.get("status") != "success":
        raise_api_error(409, "PACKAGE_FAILED", "任务尚未完成，暂时无法下载规则包", "请等待任务状态变为 success 后再下载。")

    try:
        project = ProjectService.load_project(task_id)
        generated = RulesGeneratorService.generate(project["analysis"])
        ProjectService.save_generated_rules(task_id, generated)
        buffer = _build_rules_zip(generated)
    except FileNotFoundError:
        raise_api_error(404, "TASK_NOT_FOUND")
    except Exception:
        logger.exception("规则包打包失败 task_id=%s", task_id)
        raise_api_error(500, "PACKAGE_FAILED")

    task_record = TaskDBService.get_task(task_id) or {}
    source_ref = str(task_record.get("source_ref") or project.get("source_path") or "project")
    project_name = _safe_filename(_infer_project_name(source_ref, str(project.get("source_path") or ""), task_id))
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="asgis-rules-{project_name}-{task_id}.zip"'},
    )


def _load_status_or_404(task_id: str) -> dict:
    """读取任务状态，不存在时抛标准错误。"""
    try:
        return ProjectService.load_project_status(task_id)
    except FileNotFoundError:
        raise_api_error(404, "TASK_NOT_FOUND")


def _task_status_payload(status: dict) -> dict:
    """裁剪为统一任务状态返回结构。"""
    return {
        "task_id": status.get("task_id") or status.get("project_id"),
        "status": status.get("status"),
        "stage": status.get("stage"),
        "progress": status.get("progress", 0),
        "message": status.get("message", ""),
        "error_code": status.get("error_code"),
        "error_message": status.get("error_message"),
        "created_at": status.get("created_at"),
        "updated_at": status.get("updated_at"),
    }


def _build_rules_zip(generated: dict[str, str]) -> BytesIO:
    """把四个规则文件打包为 zip。"""
    buffer = BytesIO()
    files = {
        "rules.md": generated["rules_markdown"],
        "development-flow.md": generated["development_flow"],
        ".clinerules": generated["cline_rules"],
        "cursor-rules.md": generated["cursor_rules"],
    }
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in files.items():
            zip_file.writestr(filename, content)
    buffer.seek(0)
    return buffer


def _build_task_result(task_id: str, project: dict) -> dict:
    """把内部分析结果转换成前端可直接渲染的标准结构。"""
    analysis = project.get("analysis", {})
    tech = analysis.get("tech_stack", {})
    stats = analysis.get("stats", {})
    patterns = analysis.get("patterns", {})
    generated = RulesGeneratorService.generate(analysis)
    source_type = project.get("source_type") or "zip"
    source_path = str(project.get("source_path") or "")
    task_record = TaskDBService.get_task(task_id) or {}
    source_ref = str(task_record.get("source_ref") or source_path or task_id)
    project_name = _infer_project_name(source_ref, source_path, task_id)

    return {
        "project_id": task_id,
        "project_name": project_name,
        "source_type": source_type if source_type in {"zip", "git"} else "zip",
        "tech_stack": _build_standard_tech_stack(tech),
        "summary": _build_project_summary(stats, patterns),
        "rules": _build_structured_rules(analysis),
        "files": {
            "rules_md": generated["rules_markdown"],
            "development_flow_md": generated["development_flow"],
            "cline_rules": generated["cline_rules"],
            "cursor_rules": generated["cursor_rules"],
        },
        "download_url": f"/api/tasks/{task_id}/download",
    }


def _build_standard_tech_stack(tech: dict) -> dict:
    """转换技术栈字段，前端无需理解内部字段名。"""
    return {
        "framework": tech.get("frontend") or tech.get("project_type") or "unknown",
        "language": tech.get("language") or "unknown",
        "ui_library": tech.get("ui") or "unknown",
        "state_manager": tech.get("state") or "unknown",
        "router": _detect_router_from_tech(tech),
        "build_tool": tech.get("build") or "unknown",
    }


def _detect_router_from_tech(tech: dict) -> str:
    """根据当前技术栈信息给出保守路由识别结果。"""
    evidence = " ".join(str(item) for item in tech.get("project_type_evidence", []))
    if "vue-router" in evidence.lower():
        return "Vue Router"
    if "react router" in evidence.lower():
        return "React Router"
    project_type = str(tech.get("project_type", "")).lower()
    if "uni-app" in project_type:
        return "pages.json"
    if "小程序" in project_type:
        return "app.json/pages"
    return "unknown"


def _build_project_summary(stats: dict, patterns: dict) -> dict:
    """生成项目统计摘要。"""
    api_files = patterns.get("api", {}).get("api_files", [])
    request_files = patterns.get("api", {}).get("request_files", [])
    component_files = patterns.get("components", {}).get("component_files", [])
    view_files = patterns.get("pages", {}).get("view_files", [])
    store_files = patterns.get("state", {}).get("store_files", [])
    return {
        "total_files": stats.get("file_count", 0),
        "analyzed_files": stats.get("file_count", 0),
        "api_files": len(set(api_files + request_files)),
        "component_files": len(component_files),
        "view_files": len(view_files),
        "store_files": len(store_files),
    }


def _build_structured_rules(analysis: dict) -> list[dict]:
    """把当前 recommendations 转换成结构化规则数组，后续步骤再细化为 6 类。"""
    return RulesGeneratorService.generate_rule_items(analysis)


def _infer_rule_category(rule: str) -> str:
    """根据规则文本保守推断分类。"""
    mapping = [
        ("API", "API 调用规则"),
        ("request", "API 调用规则"),
        ("store", "状态管理规则"),
        ("状态", "状态管理规则"),
        ("页面", "项目结构规则"),
        ("目录", "项目结构规则"),
        ("组件", "组件封装规则"),
        ("hooks", "组件封装规则"),
        ("composables", "组件封装规则"),
        ("权限", "路由与权限规则"),
    ]
    lower_rule = rule.lower()
    for keyword, category in mapping:
        if keyword.lower() in lower_rule:
            return category
    return "工程规范规则"


def _infer_rule_title(rule: str) -> str:
    """从规则文本生成短标题。"""
    cleaned = rule.strip().replace("。", "")
    return cleaned[:28] if cleaned else "工程规范规则"


def _infer_project_name(source_ref: str, source_path: str, task_id: str) -> str:
    """从上传文件名、Git 地址或源码路径推断项目名称。"""
    candidate = source_ref or source_path or task_id
    candidate = candidate.rstrip("/\\")
    name = candidate.split("/")[-1].split("\\")[-1] or task_id
    if name.endswith(".git"):
        name = name[:-4]
    if name.endswith(".zip"):
        name = name[:-4]
    return name or task_id


def _safe_filename(value: str) -> str:
    """生成适合放入下载文件名的项目名。"""
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value)
    return cleaned.strip("-") or "project"
