import logging
import zipfile
from io import BytesIO

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.error_model import raise_api_error
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
            raise_api_error(
                409,
                status.get("error_code") or "ANALYZE_FAILED",
                status.get("error_message") or status.get("message") or "项目分析失败，无法生成 Rules",
                status.get("suggestion") or "请先修复分析失败原因，再重新生成 Rules。",
            )
        if status.get("status") != "success":
            raise_api_error(409, "ANALYZE_FAILED", "项目仍在分析中，请等待完成后再生成 Rules", "请等待分析状态变为 success 后再生成。")

        project = ProjectService.load_project(payload.project_id)
        generated = RulesGeneratorService.generate(project["analysis"])
        ProjectService.save_generated_rules(payload.project_id, generated)
        return generated
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise_api_error(404, "TASK_NOT_FOUND")
    except Exception as exc:
        logger.exception("规则生成失败")
        raise_api_error(500, "RULE_GENERATE_FAILED")


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
            raise_api_error(404, "TASK_NOT_FOUND")
        except Exception as exc:
            logger.exception("规则包打包失败")
            raise_api_error(500, "PACKAGE_FAILED")

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
