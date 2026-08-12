"""
重试机制单元测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from backend.core.retry import (
    RetryConfig,
    FallbackConfig,
    with_retry,
    with_retry_sync,
    LLM_RETRY_CONFIG,
    LLM_FALLBACK_CONFIG,
    MEDICAL_FALLBACK_CONFIG,
)


@pytest.mark.asyncio
async def test_with_retry_success():
    """测试重试成功"""
    call_count = 0

    @with_retry(RetryConfig(max_retries=3))
    async def success_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = await success_func()
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_with_retry_failure_then_success():
    """测试重试失败后成功"""
    call_count = 0

    @with_retry(RetryConfig(max_retries=3, retry_delay=0.1))
    async def fail_then_success():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("暂时失败")
        return "success"

    result = await fail_then_success()
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_with_retry_all_failures():
    """测试所有重试失败"""
    call_count = 0

    @with_retry(
        RetryConfig(max_retries=3, retry_delay=0.1),
        FallbackConfig(fallback_response="兜底回复"),
    )
    async def always_fail():
        nonlocal call_count
        call_count += 1
        raise ValueError("始终失败")

    result = await always_fail()
    assert result == "兜底回复"
    assert call_count == 3


@pytest.mark.asyncio
async def test_with_retry_with_fallback_model():
    """测试备用模型兜底"""
    call_count = 0

    @with_retry(
        RetryConfig(max_retries=2, retry_delay=0.1),
        FallbackConfig(fallback_response="兜底回复", fallback_model="backup-model"),
    )
    async def fail_with_model(model=None):
        nonlocal call_count
        call_count += 1
        if model == "backup-model":
            return "备用模型响应"
        raise ValueError("主模型失败")

    result = await fail_with_model()
    assert result == "备用模型响应"


def test_with_retry_sync_success():
    """测试同步重试成功"""
    call_count = 0

    @with_retry_sync(RetryConfig(max_retries=3))
    def success_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = success_func()
    assert result == "success"
    assert call_count == 1


def test_with_retry_sync_failure():
    """测试同步重试失败"""
    call_count = 0

    @with_retry_sync(
        RetryConfig(max_retries=3, retry_delay=0.1),
        FallbackConfig(fallback_response="兜底回复"),
    )
    def always_fail():
        nonlocal call_count
        call_count += 1
        raise ValueError("始终失败")

    result = always_fail()
    assert result == "兜底回复"
    assert call_count == 3


def test_retry_config_defaults():
    """测试重试配置默认值"""
    config = RetryConfig()
    assert config.max_retries == 3
    assert config.retry_delay == 1.0
    assert config.backoff_factor == 2.0
    assert config.max_delay == 30.0


def test_fallback_config_defaults():
    """测试兜底配置默认值"""
    config = FallbackConfig()
    assert "抱歉" in config.fallback_response
    assert config.fallback_model is None


def test_predefined_configs():
    """测试预定义配置"""
    assert LLM_RETRY_CONFIG.max_retries == 3
    assert LLM_FALLBACK_CONFIG.fallback_response is not None
    assert MEDICAL_FALLBACK_CONFIG.fallback_response is not None
    assert "120" in MEDICAL_FALLBACK_CONFIG.fallback_response
