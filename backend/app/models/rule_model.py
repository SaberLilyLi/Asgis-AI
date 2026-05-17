from typing import Any

from pydantic import BaseModel, Field


class RepoAnalyzeRequest(BaseModel):
    """Git 仓库分析请求模型。Token 只用于本次 clone，不落盘。"""

    git_url: str = Field(..., min_length=10, description="仅允许 github.com 或 gitee.com 的 HTTPS 仓库地址")
    access_token: str | None = Field(default=None, description="GitHub / Gitee 私有仓库访问 Token")


class GenerateRulesRequest(BaseModel):
    """规则生成请求模型。"""

    project_id: str = Field(..., min_length=8, description="上传或仓库分析后返回的项目 ID")


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

