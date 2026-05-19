from typing import Any

from pydantic import BaseModel, Field


class RepoAnalyzeRequest(BaseModel):
    """Git 仓库分析请求模型。Token 只用于本次 clone，不落盘。"""

    git_url: str = Field(..., min_length=10, description="仅允许 github.com 或 gitee.com 的 HTTPS 仓库地址")
    access_token: str | None = Field(default=None, description="GitHub / Gitee 私有仓库访问 Token")


class GenerateRulesRequest(BaseModel):
    """规则生成请求模型。"""

    project_id: str = Field(..., min_length=8, description="上传或仓库分析后返回的项目 ID")


class RuleEvidence(BaseModel):
    """Single source location that supports a generated rule."""

    file: str
    line: int
    snippet: str


class PatternExample(BaseModel):
    """Compact example that illustrates a learned engineering pattern."""

    file: str
    snippet: str


class PatternItem(BaseModel):
    """Project engineering pattern learned from file structure and text signals."""

    id: str
    category: str
    name: str
    description: str
    patterns: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    occurrences: int = 0
    coverage: float = 0.0
    weight: float = 0.0
    confidence: float = 0.0
    examples: list[PatternExample] = Field(default_factory=list)


class RuleItem(BaseModel):
    """Structured rule returned to the frontend."""

    id: str
    category: str
    title: str
    description: str
    level: str
    content: str
    evidence: list[RuleEvidence] = Field(default_factory=list)
    matched_patterns: list[str] = Field(default_factory=list)
    match_count: int = 0
    confidence: float = 0.0
    quality_score: float = 0.0
    stability_score: float = 0.0
    consistency_score: float = 0.0
    conflict_detected: bool = False
    conflict_reason: str | None = None
    recommendation: str = ""
    evidence_files: list[str] = Field(default_factory=list)


class ProjectFile(BaseModel):
    """扫描出的源码文件模型。"""

    path: str
    type: str
    content: str


class PatternAnalysis(BaseModel):
    """工程规范分析结果模型。"""

    tech_stack: dict[str, Any]
    stats: dict[str, Any]
    patterns: dict[str, Any]
    recommendations: list[str]
