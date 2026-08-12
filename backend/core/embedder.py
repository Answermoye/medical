"""
医疗导诊与报告解读助手 - Embedding模块

使用BGE-M3模型生成dense和sparse向量
"""

from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.config import get_settings
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class Embedder:
    """BGE-M3 Embedding类"""

    _instance: Optional["Embedder"] = None

    def __new__(cls) -> "Embedder":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.settings = get_settings()
            self.model: SentenceTransformer | None = None
            self._initialized = True
            logger.info("Embedder初始化完成")

    def _load_model(self) -> None:
        """懒加载模型"""
        if self.model is None:
            logger.info(f"加载Embedding模型: {self.settings.EMBEDDING_MODEL}")
            self.model = SentenceTransformer(
                self.settings.EMBEDDING_MODEL,
                device=self.settings.EMBEDDING_DEVICE,
            )
            logger.info("Embedding模型加载完成")

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        生成dense向量

        Args:
            texts: 文本列表
            batch_size: 批处理大小
            show_progress: 是否显示进度

        Returns:
            dense向量矩阵
        """
        self._load_model()

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=True,
            )
            return embeddings
        except Exception as e:
            logger.error(f"Embedding编码失败: {e}")
            raise

    def encode_single(self, text: str) -> np.ndarray:
        """
        生成单条文本的dense向量

        Args:
            text: 输入文本

        Returns:
            dense向量
        """
        return self.encode([text])[0]

    def compute_similarity(
        self,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray,
    ) -> np.ndarray:
        """
        计算相似度

        Args:
            query_embedding: 查询向量
            document_embeddings: 文档向量矩阵

        Returns:
            相似度分数数组
        """
        # 余弦相似度
        similarity = np.dot(document_embeddings, query_embedding)
        return similarity

    def get_embedding_dimension(self) -> int:
        """
        获取向量维度

        Returns:
            向量维度
        """
        self._load_model()
        return self.model.get_sentence_embedding_dimension()


# 全局Embedder实例
embedder = Embedder()
