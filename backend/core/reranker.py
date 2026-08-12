"""
医疗导诊与报告解读助手 - Reranker模块

使用BGE-Reranker对检索结果重排序
"""

from typing import Optional

from sentence_transformers import CrossEncoder

from backend.config import get_settings
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class Reranker:
    """BGE-Reranker类"""

    _instance: Optional["Reranker"] = None

    def __new__(cls) -> "Reranker":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.settings = get_settings()
            self.model: CrossEncoder | None = None
            self._initialized = True
            logger.info("Reranker初始化完成")

    def _load_model(self) -> None:
        """懒加载模型"""
        if self.model is None:
            logger.info(f"加载Reranker模型: {self.settings.RERANKER_MODEL}")
            self.model = CrossEncoder(
                self.settings.RERANKER_MODEL,
                max_length=512,
            )
            logger.info("Reranker模型加载完成")

    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int | None = None,
    ) -> list[dict]:
        """
        对文档重排序

        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回数量

        Returns:
            重排序后的结果列表，包含分数和索引
        """
        self._load_model()

        if not documents:
            return []

        try:
            # 构建查询-文档对
            pairs = [(query, doc) for doc in documents]

            # 计算相关性分数
            scores = self.model.predict(pairs)

            # 构建结果
            results = []
            for idx, score in enumerate(scores):
                results.append({
                    "index": idx,
                    "score": float(score),
                    "document": documents[idx],
                })

            # 按分数降序排序
            results.sort(key=lambda x: x["score"], reverse=True)

            # 截取top_k
            if top_k:
                results = results[:top_k]

            return results

        except Exception as e:
            logger.error(f"Reranker重排序失败: {e}")
            raise

    def rerank_with_metadata(
        self,
        query: str,
        documents: list[dict],
        content_key: str = "content",
        top_k: int | None = None,
    ) -> list[dict]:
        """
        对带元数据的文档重排序

        Args:
            query: 查询文本
            documents: 文档列表，每个文档是字典
            content_key: 内容字段名
            top_k: 返回数量

        Returns:
            重排序后的结果列表
        """
        self._load_model()

        if not documents:
            return []

        try:
            # 提取文档内容
            contents = [doc.get(content_key, "") for doc in documents]

            # 构建查询-文档对
            pairs = [(query, content) for content in contents]

            # 计算相关性分数
            scores = self.model.predict(pairs)

            # 构建结果
            results = []
            for idx, score in enumerate(scores):
                result = documents[idx].copy()
                result["rerank_score"] = float(score)
                results.append(result)

            # 按分数降序排序
            results.sort(key=lambda x: x["rerank_score"], reverse=True)

            # 截取top_k
            if top_k:
                results = results[:top_k]

            return results

        except Exception as e:
            logger.error(f"Reranker重排序失败: {e}")
            raise

    def compute_score(self, query: str, document: str) -> float:
        """
        计算单个文档的相关性分数

        Args:
            query: 查询文本
            document: 文档文本

        Returns:
            相关性分数
        """
        self._load_model()

        try:
            score = self.model.predict([(query, document)])
            return float(score[0])
        except Exception as e:
            logger.error(f"计算分数失败: {e}")
            raise


# 全局Reranker实例
reranker = Reranker()
