import os
from typing import Any

from openai import OpenAI


class LLMService:
    """Qwen LLM 服务，使用 OpenAI SDK compatible mode。"""

    @staticmethod
    def build_client() -> OpenAI:
        """构建 Qwen 兼容客户端，默认读取环境变量。"""
        api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        if not api_key:
            raise RuntimeError("缺少 DASHSCOPE_API_KEY / QWEN_API_KEY / OPENAI_API_KEY")
        return OpenAI(api_key=api_key, base_url=base_url)

    @classmethod
    def generate_rules_with_qwen(cls, prompt: str) -> str:
        """调用 qwen-plus 生成规则文本，失败时由上层回退到确定性模板。"""
        client = cls.build_client()
        response: Any = client.chat.completions.create(
            model=os.getenv("QWEN_MODEL", "qwen-plus"),
            messages=[
                {"role": "system", "content": "你是严谨的工程规范分析助手，只输出固定格式 Markdown。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

