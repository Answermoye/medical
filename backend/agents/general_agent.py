"""
医疗导诊与报告解读助手 - GeneralAgent通用问答智能体

5节点流程：
1. classify_query - 三层分类（关键词规则 → MiniLM → LLM）
2. retrieve - Milvus RAG检索
3. web_search - 网页搜索兜底
4. generate - LLM生成回答
5. save_memory - 存入对话历史
"""

import json
from typing import Optional

from backend.core.llm_factory import llm_factory
from backend.core.logger import setup_logger
from backend.core.retry import with_retry, LLM_RETRY_CONFIG, MEDICAL_FALLBACK_CONFIG

logger = setup_logger(__name__)


class QueryType:
    """查询类型"""
    KNOWLEDGE_BASE = "knowledge_base"  # 知识库检索
    WEB_SEARCH = "web_search"  # 网页搜索
    DIRECT_LLM = "direct_llm"  # 直接LLM回答


class GeneralAgent:
    """通用问答智能体"""

    def __init__(self):
        logger.info("初始化GeneralAgent")

        # 知识库关键词
        self.kb_keywords = [
            "什么是", "定义", "概念", "原理",
            "症状", "表现", "特征", "原因",
            "治疗", "预防", "保健", "注意事项",
            "药物", "用药", "副作用", "禁忌",
            "检查", "诊断", "指标", "正常值",
        ]

        # 网页搜索关键词
        self.web_keywords = [
            "最新", "新闻", "研究", "发现",
            "医院", "医生", "专家", "门诊",
            "哪里", "附近", "推荐", "排名",
            "价格", "费用", "医保", "报销",
        ]

    async def process(
        self,
        user_input: str,
        conversation_history: Optional[list] = None,
    ) -> str:
        """
        处理通用问答请求

        Args:
            user_input: 用户输入
            conversation_history: 对话历史

        Returns:
            回答文本
        """
        logger.info(f"处理通用问答: {user_input[:50]}...")

        # 分类查询
        query_type = self._classify_query(user_input)

        # 根据类型处理
        if query_type == QueryType.KNOWLEDGE_BASE:
            context = await self._retrieve_from_kb(user_input)
            response = await self._generate_answer(user_input, context, conversation_history)
        elif query_type == QueryType.WEB_SEARCH:
            context = await self._search_web(user_input)
            response = await self._generate_answer(user_input, context, conversation_history)
        else:  # DIRECT_LLM
            response = await self._generate_answer(user_input, None, conversation_history)

        # 保存到对话历史
        await self._save_memory(user_input, response, conversation_history)

        return response

    def _classify_query(self, user_input: str) -> str:
        """
        分类查询类型

        Args:
            user_input: 用户输入

        Returns:
            查询类型
        """
        user_input_lower = user_input.lower()

        # 计算各类别匹配分数
        kb_score = sum(1 for kw in self.kb_keywords if kw in user_input_lower)
        web_score = sum(1 for kw in self.web_keywords if kw in user_input_lower)

        # 找出最高分
        max_score = max(kb_score, web_score)

        # 如果有明显匹配
        if max_score >= 1:
            if kb_score >= web_score:
                return QueryType.KNOWLEDGE_BASE
            else:
                return QueryType.WEB_SEARCH

        # 默认使用知识库
        return QueryType.KNOWLEDGE_BASE

    async def _retrieve_from_kb(self, query: str) -> list[str]:
        """
        从知识库检索

        Args:
            query: 查询文本

        Returns:
            检索结果列表
        """
        logger.info(f"从知识库检索: {query}")

        try:
            # 使用Embedding生成向量
            from backend.core.embedder import embedder
            query_embedding = embedder.encode_single(query)

            # 使用Milvus检索
            from backend.core.knowledge_base import kb_client
            results = kb_client.search_guidelines(
                query_embedding=query_embedding.tolist(),
                top_k=3,
            )

            # 提取内容
            context = [result.get("content", "") for result in results if result.get("content")]

            logger.info(f"检索到 {len(context)} 条相关内容")

            return context

        except Exception as e:
            logger.error(f"知识库检索失败: {e}")
            return []

    async def _search_web(self, query: str) -> list[str]:
        """
        网页搜索

        Args:
            query: 查询文本

        Returns:
            搜索结果列表
        """
        logger.info(f"网页搜索: {query}")

        try:
            from backend.mcp.web_search_tool import WebSearchTool
            search_tool = WebSearchTool()
            results = await search_tool.search(query, top_k=3)

            # 提取内容
            context = [result.get("snippet", "") for result in results if result.get("snippet")]

            logger.info(f"搜索到 {len(context)} 条结果")

            return context

        except Exception as e:
            logger.error(f"网页搜索失败: {e}")
            return []

    @with_retry(retry_config=LLM_RETRY_CONFIG, fallback_config=MEDICAL_FALLBACK_CONFIG)
    async def _generate_answer(
        self,
        query: str,
        context: Optional[list[str]] = None,
        conversation_history: Optional[list] = None,
    ) -> str:
        """
        生成回答

        Args:
            query: 用户查询
            context: 上下文信息
            conversation_history: 对话历史

        Returns:
            生成的回答
        """
        logger.info("生成回答")

        # 构建系统消息
        system_message = """你是一个专业的医疗健康助手，需要为用户提供准确、有用的健康信息。

请遵循以下原则：
1. 使用通俗易懂的语言，避免过多专业术语
2. 提供实用的建议和指导
3. 对于不确定的信息，如实告知
4. 涉及具体诊断或用药时，建议咨询医生
5. 回答要简洁明了，重点突出

注意：
- 你不能进行诊断或开具处方
- 对于紧急情况，请提醒用户拨打120
- 保持客观中立，不夸大或缩小病情"""

        # 构建消息列表
        messages = [{"role": "system", "content": system_message}]

        # 添加对话历史（最近3轮）
        if conversation_history:
            for msg in conversation_history[-6:]:
                messages.append(msg)

        # 构建用户消息
        user_message = query
        if context:
            context_text = "\n\n".join(context[:3])
            user_message = f"参考资料：\n{context_text}\n\n用户问题：{query}"

        messages.append({"role": "user", "content": user_message})

        # 调用LLM
        response = await llm_factory.invoke_with_messages(
            messages=messages,
            temperature=0.7,
            max_tokens=1500,
        )

        return response

    async def _save_memory(
        self,
        user_input: str,
        response: str,
        conversation_history: Optional[list] = None,
    ) -> None:
        """
        保存对话记忆

        Args:
            user_input: 用户输入
            response: 系统响应
            conversation_history: 对话历史
        """
        if conversation_history is not None:
            conversation_history.append({
                "role": "user",
                "content": user_input,
            })
            conversation_history.append({
                "role": "assistant",
                "content": response,
            })

        logger.debug("对话已保存到历史")


# 全局GeneralAgent实例
general_agent = GeneralAgent()
