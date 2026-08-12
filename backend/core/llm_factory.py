"""
医疗导诊与报告解读助手 - LLM工厂模块

支持通义千问等LLM的统一调用接口
"""

import asyncio
from typing import AsyncGenerator, Dict, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from backend.config import get_settings
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class LLMFactory:
    """LLM工厂类 - 统一管理LLM实例"""

    _instance: Optional["LLMFactory"] = None
    _llm_cache: Dict[str, ChatOpenAI] = {}

    def __new__(cls) -> "LLMFactory":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.settings = get_settings()
            self._initialized = True
            logger.info("LLMFactory初始化完成")

    def get_llm(
        self,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        streaming: bool = False,
    ) -> ChatOpenAI:
        """
        获取LLM实例

        Args:
            model: 模型名称，默认使用配置中的模型
            temperature: 温度参数
            max_tokens: 最大token数
            streaming: 是否启用流式输出

        Returns:
            ChatOpenAI实例
        """
        model = model or self.settings.QWEN_MODEL
        cache_key = f"{model}_{temperature}_{max_tokens}_{streaming}"

        if cache_key not in self._llm_cache:
            self._llm_cache[cache_key] = ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
                openai_api_key=self.settings.QWEN_API_KEY,
                openai_api_base=self.settings.QWEN_BASE_URL,
            )
            logger.debug(f"创建LLM实例: model={model}, temp={temperature}")

        return self._llm_cache[cache_key]

    async def invoke(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        调用LLM生成响应

        Args:
            prompt: 用户提示
            system_message: 系统消息
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            生成的文本
        """
        llm = self.get_llm(model=model, temperature=temperature, max_tokens=max_tokens)

        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))

        try:
            result = await llm.ainvoke(messages)
            return result.content
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    async def stream(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """
        流式调用LLM

        Args:
            prompt: 用户提示
            system_message: 系统消息
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数

        Yields:
            生成的文本片段
        """
        llm = self.get_llm(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=True,
        )

        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))

        try:
            async for chunk in llm.astream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"LLM流式调用失败: {e}")
            raise

    async def invoke_with_messages(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        使用消息列表调用LLM

        Args:
            messages: 消息列表，格式: [{"role": "user/system/assistant", "content": "..."}]
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            生成的文本
        """
        llm = self.get_llm(model=model, temperature=temperature, max_tokens=max_tokens)

        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                langchain_messages.append(HumanMessage(content=content))

        try:
            result = await llm.ainvoke(langchain_messages)
            return result.content
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    def clear_cache(self) -> None:
        """清除LLM缓存"""
        self._llm_cache.clear()
        logger.info("LLM缓存已清除")


# 全局LLM工厂实例
llm_factory = LLMFactory()
