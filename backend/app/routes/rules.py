import logging
import zipfile
from io import BytesIO

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.rule_model import GenerateRulesRequest
from app.services.project_service import ProjectService
from app.services.rules_generator_service import RulesGeneratorService


logger = logging.getLogger(__name__)
router = APIRouter(tags=["rules"])


@router.post("/generate_rules")
def generate_rules(payload: GenerateRulesRequest) -> dict:
    """根据已保存的项目分析结果生成 AI Coding Rules。"""
    try:
        status = ProjectService.load_project_status(payload.project_id)
        if status.get("status") == "failed":
            raise HTTPException(
                status_code=409,
                detail={
                    "code": status.get("code", "ANALYSIS_FAILED"),
                    "message": status.get("message", "项目分析失败，无法生成 Rules"),
                    "suggestion": status.get("suggestion", "请先修复分析失败原因，再重新生成 Rules。"),
                },
            )
        if status.get("status") != "success":
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "ANALYSIS_NOT_READY",
                    "message": "项目仍在分析中，请等待完成后再生成 Rules",
                    "suggestion": "请等待分析状态变为已完成。",
                },
            )

        project = ProjectService.load_project(payload.project_id)
        generated = RulesGeneratorService.generate(project["analysis"])
        ProjectService.save_generated_rules(payload.project_id, generated)
        return generated
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": "project_id 不存在或尚未分析",
                "suggestion": "请重新上传项目或重新创建仓库分析任务。",
            },
        ) from exc
    except Exception as exc:
        logger.exception("规则生成失败")
        raise HTTPException(status_code=500, detail="规则生成失败") from exc


@router.get("/download_rules_package/{project_id}")
def download_rules_package(project_id: str) -> StreamingResponse:
    """下载 rules.md、development-flow.md、.clinerules、cursor-rules.md 的 zip 包。"""
    output_dir = ProjectService.get_project_output_dir(project_id)
    files = ["rules.md", "development-flow.md", ".clinerules", "cursor-rules.md"]
    if not output_dir.exists() or not all((output_dir / name).exists() for name in files):
        try:
            project = ProjectService.load_project(project_id)
            generated = RulesGeneratorService.generate(project["analysis"])
            ProjectService.save_generated_rules(project_id, generated)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="project_id 不存在或尚未分析") from exc

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for name in files:
            path = output_dir / name
            if path.exists():
                zip_file.write(path, arcname=name)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="asgis-rules-{project_id}.zip"'},
    )

