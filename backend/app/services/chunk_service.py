class ChunkService:
    """文本切片服务，为后续 RAG 或 LLM 分析预留能力。"""

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1800, overlap: int = 200) -> list[str]:
        """按固定窗口切分文本，保留少量重叠上下文。"""
        if not text:
            return []
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            if end == len(text):
                break
            start = max(0, end - overlap)
        return chunks

