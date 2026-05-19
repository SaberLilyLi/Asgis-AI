import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PatternSpec:
    """Lightweight text or regex pattern used by the Evidence Chain MVP."""

    name: str
    value: str
    is_regex: bool = False
    case_sensitive: bool = False


class PatternMatcherService:
    """Find simple path and source-text evidence without AST parsing."""

    SUPPORTED_SUFFIXES = {".vue", ".ts", ".tsx", ".js", ".jsx", ".json", ".md"}
    IGNORE_DIRS = {"node_modules", "dist", "build", ".git", "coverage"}

    @classmethod
    def find_matches(cls, files: list[dict[str, str]], patterns: list[PatternSpec]) -> list[dict[str, Any]]:
        """Return source-line matches for the given patterns."""
        matches: list[dict[str, Any]] = []
        for file_info in files:
            path = str(file_info.get("path", ""))
            if not cls._should_scan(path):
                continue
            content = str(file_info.get("content", ""))
            for pattern in patterns:
                matches.extend(cls._match_file(path, content, pattern))
        return matches

    @classmethod
    def find_path_matches(cls, files: list[dict[str, str]], patterns: list[PatternSpec]) -> list[dict[str, Any]]:
        """Return file-level matches for path-only features."""
        matches: list[dict[str, Any]] = []
        for file_info in files:
            path = str(file_info.get("path", ""))
            if not cls._should_scan(path):
                continue
            for pattern in patterns:
                if cls._matches_text(path, pattern):
                    matches.append(
                        {
                            "file": path,
                            "line": 1,
                            "snippet": path,
                            "pattern": pattern.name,
                        }
                    )
        return matches

    @classmethod
    def _match_file(cls, path: str, content: str, pattern: PatternSpec) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            if cls._matches_text(line, pattern):
                matches.append(
                    {
                        "file": path,
                        "line": line_number,
                        "snippet": line.strip(),
                        "pattern": pattern.name,
                    }
                )
        return matches

    @classmethod
    def _matches_text(cls, text: str, pattern: PatternSpec) -> bool:
        flags = 0 if pattern.case_sensitive else re.IGNORECASE
        if pattern.is_regex:
            return re.search(pattern.value, text, flags) is not None
        if pattern.case_sensitive:
            return pattern.value in text
        return pattern.value.lower() in text.lower()

    @classmethod
    def _should_scan(cls, path: str) -> bool:
        normalized = path.replace("\\", "/")
        parts = normalized.split("/")
        if any(part in cls.IGNORE_DIRS for part in parts):
            return False
        return any(normalized.endswith(suffix) for suffix in cls.SUPPORTED_SUFFIXES)
