from pathlib import Path


class ScanService:
    """项目扫描服务，负责读取源码文件并跳过无关目录。"""

    IGNORE_DIRS = {"node_modules", "dist", ".git", ".idea", ".vscode", "coverage", ".output"}
    TEXT_SUFFIXES = {
        ".vue",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".json",
        ".md",
        ".scss",
        ".css",
        ".less",
        ".sass",
        ".wxml",
        ".wxss",
        ".wxs",
        ".axml",
        ".acss",
        ".swan",
        ".ttml",
        ".ttss",
        ".py",
        ".yml",
        ".yaml",
    }
    MAX_FILE_BYTES = 512 * 1024
    MAX_SCAN_FILES = 5000

    @classmethod
    def scan_project(cls, root: Path) -> list[dict[str, str]]:
        """扫描项目目录，返回 path、type、content 三元信息。"""
        files: list[dict[str, str]] = []
        matched_files = 0
        for path in root.rglob("*"):
            if not path.is_file() or cls._is_ignored(path):
                continue
            if path.suffix.lower() not in cls.TEXT_SUFFIXES:
                continue
            matched_files += 1
            if matched_files > cls.MAX_SCAN_FILES:
                raise ValueError(f"可分析源码文件超过 {cls.MAX_SCAN_FILES} 个，请缩小项目范围后重试")
            if path.stat().st_size > cls.MAX_FILE_BYTES:
                continue
            relative_path = path.relative_to(root).as_posix()
            files.append(
                {
                    "path": relative_path,
                    "type": cls._detect_type(path),
                    "content": path.read_text(encoding="utf-8", errors="ignore"),
                }
            )
        return files

    @classmethod
    def _is_ignored(cls, path: Path) -> bool:
        """判断文件路径是否命中忽略目录。"""
        return any(part in cls.IGNORE_DIRS for part in path.parts)

    @staticmethod
    def _detect_type(path: Path) -> str:
        """根据后缀识别文件类型。"""
        suffix = path.suffix.lower()
        if suffix == ".vue":
            return "vue"
        if suffix in {".ts", ".tsx"}:
            return "typescript"
        if suffix in {".js", ".jsx"}:
            return "javascript"
        if suffix in {".wxml", ".axml", ".swan", ".ttml"}:
            return "miniapp-template"
        if suffix in {".wxss", ".acss", ".ttss"}:
            return "miniapp-style"
        return suffix.removeprefix(".") or "text"
