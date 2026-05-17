from typing import Any


class PromptService:
    """Prompt 构建服务，为 Qwen 生成规则提供强约束输入。"""

    @staticmethod
    def build_rules_prompt(analysis: dict[str, Any]) -> str:
        """构建固定格式、禁止胡说的 Rules 生成 Prompt。"""
        return f"""你是 Asgis AI 工程规范分析助手。

请严格基于以下 Pattern Analysis JSON 生成 Markdown，不允许编造未出现的目录、组件、接口或技术栈。

强约束：
1. 只输出 Markdown。
2. 必须包含：项目技术栈、工程规范、AI Coding Rules、禁止规则。
3. 规则必须工程化、可执行、适合约束 Cline / Cursor。
4. 如果分析结果中某项未识别，必须写“未识别，新增代码需遵循项目已有模式”。
5. 禁止添加 AST、Agent、自动改代码、自动 PR 等 MVP 之外能力。

Pattern Analysis JSON：
{analysis}
"""

