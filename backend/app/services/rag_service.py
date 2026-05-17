class RagService:
    """RAG 预留服务，MVP 阶段不参与主流程。"""

    @staticmethod
    def is_enabled() -> bool:
        """返回 RAG 是否启用，第一阶段默认关闭。"""
        return False

