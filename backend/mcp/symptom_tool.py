"""
症状检索工具 - FastMCP实现

提供症状→科室的语义检索功能
"""

from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class SymptomTool:
    """症状检索工具"""

    def __init__(self):
        logger.info("初始化SymptomTool")

    async def search(self, symptoms: list[str], top_k: int = 5) -> list[dict]:
        """
        搜索症状对应的科室

        Args:
            symptoms: 症状列表
            top_k: 返回结果数量

        Returns:
            科室推荐列表
        """
        # TODO: 实现Milvus混合检索
        logger.info(f"搜索症状: {symptoms}")
        return []
