import os
import shutil
import stat
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse


@dataclass(frozen=True)
class RepoError:
    """标准化仓库错误。"""

    code: str
    message: str
    suggestion: str


class RepoService:
    """Git 仓库服务，负责 URL 校验、Token clone 和安全限制。"""

    CLONE_TIMEOUT_SECONDS = 180
    MAX_REPO_BYTES = 200 * 1024 * 1024
    ALLOWED_HOSTS = {"github.com", "gitee.com"}

    @classmethod
    def clone_repo(cls, git_url: str, target_dir: Path, access_token: str | None = None) -> None:
        """克隆受信任平台仓库到目标目录，Token 只参与本次 clone，不落盘。"""
        cls.validate_repo_url(git_url)
        target_dir.mkdir(parents=True, exist_ok=True)
        clone_dir = target_dir.parent / f"clone_tmp_{uuid.uuid4().hex}"

        try:
            clone_url = cls._build_clone_url(git_url, access_token)
            cls._run_git_clone(clone_url, clone_dir)
            repo_size = cls._directory_size(clone_dir)
            if repo_size > cls.MAX_REPO_BYTES:
                raise ValueError("REPO_TOO_LARGE")
            cls._move_clone_to_target(clone_dir, target_dir)
        except TimeoutError:
            raise
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(cls.classify_clone_error(str(exc)).message) from exc
        finally:
            cls._safe_rmtree(clone_dir)

    @staticmethod
    def validate_repo_url(git_url: str) -> None:
        """只允许 GitHub / Gitee HTTPS 仓库地址，禁止 file、ssh、git@。"""
        parsed = urlparse(git_url)
        if parsed.scheme != "https":
            raise ValueError("仅允许 HTTPS 仓库地址")
        if parsed.hostname not in RepoService.ALLOWED_HOSTS:
            raise ValueError("仅允许 github.com 或 gitee.com 仓库")
        if not parsed.path or parsed.path.count("/") < 2:
            raise ValueError("仓库地址格式无效")
        if git_url.startswith(("file://", "ssh://", "git@")):
            raise ValueError("禁止 file、ssh 或 git@ 协议")

    @staticmethod
    def classify_clone_error(message: str) -> RepoError:
        """将 Git 底层错误转换成企业化错误码。"""
        lower_message = message.lower()
        if any(
            text in lower_message
            for text in [
                "authentication failed",
                "could not read username",
                "terminal prompts disabled",
                "no such device or address",
                "cannot spawn sh",
                "failed to execute prompt script",
            ]
        ):
            return RepoError(
                "PRIVATE_REPO_DENIED",
                "仓库需要登录或 Token",
                "请填写 GitHub/Gitee 访问 Token，或确认仓库为公开仓库。",
            )
        if "repository not found" in lower_message or "not found" in lower_message:
            return RepoError("PRIVATE_REPO_DENIED", "仓库不存在或无权限访问", "请检查仓库地址、大小写、可见性和访问权限。")
        if "could not resolve host" in lower_message or "failed to connect" in lower_message:
            return RepoError("REPO_CLONE_FAILED", "无法连接仓库平台", "请检查网络、代理、防火墙或稍后重试。")
        if "early eof" in lower_message or "remote end hung up" in lower_message:
            return RepoError("REPO_CLONE_FAILED", "仓库下载中断", "请稍后重试，或确认仓库体积是否过大。")
        if "permission denied" in lower_message or "access is denied" in lower_message or "winerror 5" in lower_message or "拒绝访问" in message:
            return RepoError("LOCAL_FILE_LOCKED", "本机临时目录文件被占用或拒绝访问", "请稍后重试，必要时关闭杀毒软件对项目目录的实时扫描。")
        if "repo_too_large" in lower_message or "体积超过限制" in message:
            return RepoError("REPO_TOO_LARGE", "仓库体积超过限制", "请缩小仓库体积，或改用只包含前端工程的 zip 上传。")
        return RepoError("REPO_CLONE_FAILED", "仓库分析失败", "请确认仓库存在、权限可访问且网络正常。")

    @classmethod
    def _run_git_clone(cls, clone_url: str, clone_dir: Path) -> None:
        """使用受控 git 子进程执行 clone，禁止交互式凭证弹窗。"""
        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"}
        try:
            result = subprocess.run(
                ["git", "clone", "--depth=1", clone_url, str(clone_dir)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                timeout=cls.CLONE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("仓库克隆超时，请确认仓库体积和网络状态") from exc
        if result.returncode != 0:
            message = result.stderr or result.stdout or "Git clone failed"
            raise ValueError(cls.classify_clone_error(message).message)

    @staticmethod
    def _build_clone_url(git_url: str, access_token: str | None) -> str:
        """把 Token 临时注入 clone URL，不写入任何持久化文件。"""
        if not access_token:
            return git_url
        parsed = urlparse(git_url)
        token = quote(access_token, safe="")
        if parsed.hostname == "github.com":
            netloc = f"x-access-token:{token}@{parsed.netloc}"
        elif parsed.hostname == "gitee.com":
            netloc = f"oauth2:{token}@{parsed.netloc}"
        else:
            netloc = parsed.netloc
        return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))

    @staticmethod
    def _directory_size(path: Path) -> int:
        """计算目录总体积，用于限制超大仓库。"""
        if not path.exists():
            return 0
        return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())

    @classmethod
    def _move_clone_to_target(cls, clone_dir: Path, target_dir: Path) -> None:
        """将临时 clone 目录中的源码文件移动到正式源码目录，跳过 .git。"""
        for child in target_dir.iterdir():
            if child.is_dir():
                cls._safe_rmtree(child)
            else:
                child.unlink(missing_ok=True)
        for child in clone_dir.iterdir():
            if child.name == ".git":
                continue
            shutil.move(str(child), str(target_dir / child.name))

    @classmethod
    def _safe_rmtree(cls, path: Path) -> None:
        """兼容 Windows 只读文件和短暂锁定的安全删除。"""
        if not path.exists():
            return
        try:
            shutil.rmtree(path, onerror=cls._handle_remove_readonly)
        except OSError:
            pass

    @staticmethod
    def _handle_remove_readonly(func, path: str, _exc_info) -> None:
        """清理只读文件时先恢复写权限再重试。"""
        os.chmod(path, stat.S_IWRITE)
        func(path)
