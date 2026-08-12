"""
医学指南检索工具 - FastMCP实现

提供医学指南的RAG检索功能
"""

from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class GuidelineTool:
    """医学指南检索工具"""

    def __init__(self):
        logger.info("初始化GuidelineTool")

    async def search(self, query: str, top_k: int = 3) -> list[str]:
        """
        检索相关医学指南

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            相关指南内容列表
        """
        # TODO: 实现Milvus RAG检索
        logger.info(f"检索医学指南: {query}")
        return []
