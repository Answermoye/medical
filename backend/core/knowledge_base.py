"""
医疗导诊与报告解读助手 - Milvus向量库客户端

封装Milvus连接、集合管理、向量检索等操作
"""

from typing import Any, List, Optional

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    MilvusClient,
    connections,
    utility,
)

from backend.config import get_settings
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class KnowledgeBaseClient:
    """Milvus向量库客户端"""

    _instance: Optional["KnowledgeBaseClient"] = None

    def __new__(cls) -> "KnowledgeBaseClient":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.settings = get_settings()
            self.client: MilvusClient | None = None
            self._connected = False
            self._initialized = True
            logger.info("KnowledgeBaseClient初始化完成")

    def connect(self) -> None:
        """连接Milvus"""
        if not self._connected:
            try:
                connections.connect(
                    alias="default",
                    host=self.settings.MILVUS_HOST,
                    port=self.settings.MILVUS_PORT,
                )
                self._connected = True
                logger.info(f"Milvus连接成功: {self.settings.MILVUS_HOST}:{self.settings.MILVUS_PORT}")
            except Exception as e:
                logger.error(f"Milvus连接失败: {e}")
                raise

    def disconnect(self) -> None:
        """断开Milvus连接"""
        if self._connected:
            connections.disconnect("default")
            self._connected = False
            logger.info("Milvus连接已断开")

    def create_symptom_collection(self, dimension: int = 1024) -> Collection:
        """
        创建症状科室映射集合

        Args:
            dimension: 向量维度

        Returns:
            Collection实例
        """
        self.connect()

        collection_name = "symptom_department"

        # 检查集合是否已存在
        if utility.has_collection(collection_name):
            logger.info(f"集合 {collection_name} 已存在")
            return Collection(collection_name)

        # 定义字段
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="symptom", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="department", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
        ]

        # 创建集合
        schema = CollectionSchema(fields=fields, description="症状科室映射")
        collection = Collection(name=collection_name, schema=schema)

        # 创建索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        }
        collection.create_index(field_name="embedding", index_params=index_params)

        logger.info(f"集合 {collection_name} 创建成功")
        return collection

    def create_guideline_collection(self, dimension: int = 1024) -> Collection:
        """
        创建医学指南集合

        Args:
            dimension: 向量维度

        Returns:
            Collection实例
        """
        self.connect()

        collection_name = "medical_guideline"

        # 检查集合是否已存在
        if utility.has_collection(collection_name):
            logger.info(f"集合 {collection_name} 已存在")
            return Collection(collection_name)

        # 定义字段
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=10000),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
        ]

        # 创建集合
        schema = CollectionSchema(fields=fields, description="医学指南")
        collection = Collection(name=collection_name, schema=schema)

        # 创建索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        }
        collection.create_index(field_name="embedding", index_params=index_params)

        logger.info(f"集合 {collection_name} 创建成功")
        return collection

    def insert_symptoms(
        self,
        symptoms: list[str],
        departments: list[str],
        descriptions: list[str],
        embeddings: list[list[float]],
    ) -> list[int]:
        """
        插入症状数据

        Args:
            symptoms: 症状列表
            departments: 科室列表
            descriptions: 描述列表
            embeddings: 向量列表

        Returns:
            插入的ID列表
        """
        collection = self.create_symptom_collection()

        data = [symptoms, departments, descriptions, embeddings]
        result = collection.insert(data)

        logger.info(f"插入 {len(symptoms)} 条症状数据")
        return result.primary_keys

    def insert_guidelines(
        self,
        titles: list[str],
        contents: list[str],
        sources: list[str],
        categories: list[str],
        embeddings: list[list[float]],
    ) -> list[int]:
        """
        插入指南数据

        Args:
            titles: 标题列表
            contents: 内容列表
            sources: 来源列表
            categories: 分类列表
            embeddings: 向量列表

        Returns:
            插入的ID列表
        """
        collection = self.create_guideline_collection()

        data = [titles, contents, sources, categories, embeddings]
        result = collection.insert(data)

        logger.info(f"插入 {len(titles)} 条指南数据")
        return result.primary_keys

    def search_symptoms(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        output_fields: Optional[List[str]] = None,
    ) -> list[dict[str, Any]]:
        """
        搜索症状

        Args:
            query_embedding: 查询向量
            top_k: 返回数量
            output_fields: 输出字段

        Returns:
            搜索结果列表
        """
        collection = self.create_symptom_collection()
        collection.load()

        if output_fields is None:
            output_fields = ["symptom", "department", "description"]

        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 16},
        }

        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=output_fields,
        )

        # 格式化结果
        formatted_results = []
        for hits in results:
            for hit in hits:
                result = {
                    "score": hit.score,
                    "id": hit.id,
                }
                for field in output_fields:
                    result[field] = hit.entity.get(field)
                formatted_results.append(result)

        return formatted_results

    def search_guidelines(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        output_fields: Optional[List[str]] = None,
    ) -> list[dict[str, Any]]:
        """
        搜索医学指南

        Args:
            query_embedding: 查询向量
            top_k: 返回数量
            output_fields: 输出字段

        Returns:
            搜索结果列表
        """
        collection = self.create_guideline_collection()
        collection.load()

        if output_fields is None:
            output_fields = ["title", "content", "source", "category"]

        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 16},
        }

        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=output_fields,
        )

        # 格式化结果
        formatted_results = []
        for hits in results:
            for hit in hits:
                result = {
                    "score": hit.score,
                    "id": hit.id,
                }
                for field in output_fields:
                    result[field] = hit.entity.get(field)
                formatted_results.append(result)

        return formatted_results

    def get_collection_stats(self, collection_name: str) -> dict[str, Any]:
        """
        获取集合统计信息

        Args:
            collection_name: 集合名称

        Returns:
            统计信息字典
        """
        self.connect()

        if not utility.has_collection(collection_name):
            return {"exists": False}

        collection = Collection(collection_name)
        collection.flush()

        return {
            "exists": True,
            "name": collection_name,
            "num_entities": collection.num_entities,
            "schema": str(collection.schema),
        }


# 全局KnowledgeBaseClient实例
kb_client = KnowledgeBaseClient()
