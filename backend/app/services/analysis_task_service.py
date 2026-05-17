import logging
import zipfile
from pathlib import Path

from app.services.pattern_analyzer_service import PatternAnalyzerService
from app.services.project_service import ProjectService
from app.services.repo_service import RepoService
from app.services.scan_service import ScanService


logger = logging.getLogger(__name__)


class AnalysisTaskService:
    """后台分析任务服务，统一处理上传项目和仓库项目的进度状态。"""

    @classmethod
    def analyze_zip_project(cls, project_id: str, zip_path: Path, project_root: Path) -> None:
        """后台解压 zip 并执行扫描、分析、结果落盘。"""
        try:
            ProjectService.update_project_status(project_id, "running", "extracting", 20, "正在解压 zip 项目", code="EXTRACTING")
            cls._safe_extract_zip(zip_path, project_root)

            ProjectService.update_project_status(project_id, "running", "scanning", 55, "正在扫描项目目录", code="SCANNING")
            files = ScanService.scan_project(project_root)
            if not files:
                raise ValueError("未扫描到可分析的前端源码文件")

            ProjectService.update_project_status(project_id, "running", "analyzing", 80, "正在抽取工程规范", code="ANALYZING")
            analysis = PatternAnalyzerService.analyze(files)
            ProjectService.save_project_analysis(project_id, "zip", str(project_root), analysis)
            logger.info("zip 项目分析完成 project_id=%s files=%s", project_id, len(files))
        except zipfile.BadZipFile as exc:
            cls._mark_failed(project_id, "ZIP_INVALID", "zip 文件格式无效", "请重新压缩项目后上传。", exc)
        except ValueError as exc:
            cls._mark_failed(project_id, "PROJECT_ANALYSIS_FAILED", str(exc), "请检查项目内容后重试。", exc)
        except Exception as exc:
            cls._mark_failed(project_id, "PROJECT_ANALYSIS_FAILED", "上传项目分析失败", "请检查 zip 内容或稍后重试。", exc)

    @classmethod
    def analyze_repo_project(cls, project_id: str, git_url: str, repo_dir: Path, access_token: str | None = None) -> None:
        """后台克隆仓库并执行扫描、分析、结果落盘。"""
        try:
            ProjectService.update_project_status(project_id, "running", "cloning", 25, "正在克隆远程仓库", code="CLONING")
            try:
                RepoService.clone_repo(git_url, repo_dir, access_token)
            except TimeoutError as exc:
                cls._mark_failed(project_id, "REPO_CLONE_TIMEOUT", "仓库克隆超时", "请确认仓库体积和网络状态后重试。", exc)
                return
            except ValueError as exc:
                repo_error = RepoService.classify_clone_error(str(exc))
                cls._mark_failed(project_id, repo_error.code, repo_error.message, repo_error.suggestion, exc)
                return

            ProjectService.update_project_status(project_id, "running", "scanning", 60, "正在扫描项目目录", code="SCANNING")
            files = ScanService.scan_project(repo_dir)
            if not files:
                cls._mark_failed(
                    project_id,
                    "PROJECT_NO_SOURCE",
                    "仓库中未扫描到可分析的前端源码文件",
                    "请确认仓库包含 Vue、React、小程序或 uni-app 源码，或改用 zip 上传。",
                    ValueError("no analyzable source files"),
                )
                return

            ProjectService.update_project_status(project_id, "running", "analyzing", 85, "正在抽取工程规范", code="ANALYZING")
            analysis = PatternAnalyzerService.analyze(files)
            ProjectService.save_project_analysis(project_id, "git", str(repo_dir), analysis)
            logger.info("仓库分析完成 project_id=%s url=%s files=%s", project_id, git_url, len(files))
        except ValueError as exc:
            cls._mark_failed(project_id, "PROJECT_ANALYSIS_FAILED", str(exc), "请检查仓库源码结构后重试。", exc)
        except Exception as exc:
            cls._mark_failed(project_id, "REPO_ANALYSIS_FAILED", "仓库分析失败", "请确认仓库存在、权限可访问且网络正常。", exc)

    @staticmethod
    def _safe_extract_zip(zip_path: Path, target_dir: Path) -> None:
        """安全解压 zip，阻止路径穿越和异常大文件数量。"""
        target_dir.mkdir(parents=True, exist_ok=True)
        resolved_target = target_dir.resolve()

        with zipfile.ZipFile(zip_path) as zip_file:
            members = zip_file.infolist()
            if len(members) > 8000:
                raise ValueError("zip 文件数量过多，疑似压缩包炸弹")
            for member in members:
                member_path = (target_dir / member.filename).resolve()
                if not str(member_path).startswith(str(resolved_target)):
                    raise ValueError("zip 内存在非法路径")
                if member.file_size > ScanService.MAX_FILE_BYTES * 8:
                    continue
            zip_file.extractall(target_dir)

    @staticmethod
    def _mark_failed(project_id: str, code: str, message: str, suggestion: str, exc: Exception) -> None:
        """记录失败状态并写入日志。"""
        logger.exception("项目分析失败 project_id=%s code=%s reason=%s", project_id, code, message)
        ProjectService.update_project_status(
            project_id=project_id,
            status="failed",
            stage="failed",
            progress=100,
            message=message,
            code=code,
            suggestion=suggestion,
            error=message,
        )
