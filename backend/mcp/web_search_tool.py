"""
网页搜索工具 - FastMCP实现

提供网页搜索兜底功能
"""

from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class WebSearchTool:
    """网页搜索工具"""

    def __init__(self):
        logger.info("初始化WebSearchTool")

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        网页搜索

        Args:
            query: 搜索查询
            top_k: 返回结果数量

        Returns:
            搜索结果列表
        """
        # TODO: 实现网页搜索
        logger.info(f"网页搜索: {query}")
        return []
