"""
LLMFactory单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.core.llm_factory import LLMFactory


@pytest.fixture
def llm_factory():
    """创建LLMFactory实例"""
    # 清除单例缓存
    LLMFactory._instance = None
    return LLMFactory()


def test_llm_factory_singleton():
    """测试LLMFactory单例模式"""
    LLMFactory._instance = None
    factory1 = LLMFactory()
    factory2 = LLMFactory()
    assert factory1 is factory2


def test_llm_factory_get_llm(llm_factory):
    """测试获取LLM实例"""
    llm = llm_factory.get_llm()
    assert llm is not None


def test_llm_factory_get_llm_with_params(llm_factory):
    """测试使用参数获取LLM实例"""
    llm = llm_factory.get_llm(
        model="qwen-turbo",
        temperature=0.5,
        max_tokens=1024,
        streaming=True,
    )
    assert llm is not None


def test_llm_factory_cache(llm_factory):
    """测试LLM缓存"""
    llm1 = llm_factory.get_llm()
    llm2 = llm_factory.get_llm()
    assert llm1 is llm2


def test_llm_factory_clear_cache(llm_factory):
    """测试清除缓存"""
    llm1 = llm_factory.get_llm()
    llm_factory.clear_cache()
    llm2 = llm_factory.get_llm()
    # 清除缓存后应该创建新实例
    assert llm1 is not llm2


@pytest.mark.asyncio
async def test_llm_factory_invoke(llm_factory):
    """测试LLM调用"""
    mock_response = MagicMock()
    mock_response.content = "测试响应"

    with patch.object(llm_factory, "get_llm") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        result = await llm_factory.invoke("测试提示")
        assert result == "测试响应"


@pytest.mark.asyncio
async def test_llm_factory_invoke_with_system_message(llm_factory):
    """测试带系统消息的LLM调用"""
    mock_response = MagicMock()
    mock_response.content = "测试响应"

    with patch.object(llm_factory, "get_llm") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        result = await llm_factory.invoke(
            "测试提示",
            system_message="你是一个医疗助手",
        )
        assert result == "测试响应"


@pytest.mark.asyncio
async def test_llm_factory_invoke_with_messages(llm_factory):
    """测试使用消息列表调用LLM"""
    mock_response = MagicMock()
    mock_response.content = "测试响应"

    with patch.object(llm_factory, "get_llm") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        messages = [
            {"role": "system", "content": "你是一个医疗助手"},
            {"role": "user", "content": "你好"},
        ]
        result = await llm_factory.invoke_with_messages(messages)
        assert result == "测试响应"
