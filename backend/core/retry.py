"""
医疗导诊与报告解读助手 - 三层重试兜底机制

实现LLM调用的三层重试兜底策略：
1. 第一层：正常重试（网络抖动等临时错误）
2. 第二层：降级重试（切换到备用模型）
3. 第三层：兜底回复（返回预设响应）
"""

import asyncio
import functools
from typing import Any, Callable, Optional, TypeVar, Tuple, Type

from backend.core.logger import setup_logger

logger = setup_logger(__name__)

T = TypeVar("T")


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 30.0,
        retryable_errors: Optional[Tuple[Type[Exception], ...]] = None,
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.retryable_errors = retryable_errors or (Exception,)


class FallbackConfig:
    """兜底配置"""

    def __init__(
        self,
        fallback_response: str = "抱歉，系统暂时无法处理您的请求，请稍后重试。",
        fallback_model: Optional[str] = None,
    ):
        self.fallback_response = fallback_response
        self.fallback_model = fallback_model


def with_retry(
    retry_config: Optional[RetryConfig] = None,
    fallback_config: Optional[FallbackConfig] = None,
) -> Callable:
    """
    三层重试兜底装饰器

    Args:
        retry_config: 重试配置
        fallback_config: 兜底配置

    Returns:
        装饰器函数
    """
    if retry_config is None:
        retry_config = RetryConfig()
    if fallback_config is None:
        fallback_config = FallbackConfig()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None

            # 第一层：正常重试
            for attempt in range(retry_config.max_retries):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"第{attempt + 1}次尝试成功")
                    return result

                except retry_config.retryable_errors as e:
                    last_error = e
                    if attempt < retry_config.max_retries - 1:
                        delay = min(
                            retry_config.retry_delay * (retry_config.backoff_factor ** attempt),
                            retry_config.max_delay,
                        )
                        logger.warning(
                            f"第{attempt + 1}次尝试失败: {e}, "
                            f"{delay:.1f}秒后重试..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.warning(
                            f"第{attempt + 1}次尝试失败: {e}, "
                            f"尝试降级处理..."
                        )

            # 第二层：降级重试（切换备用模型）
            if fallback_config.fallback_model:
                try:
                    logger.info(f"切换到备用模型: {fallback_config.fallback_model}")
                    kwargs["model"] = fallback_config.fallback_model
                    result = await func(*args, **kwargs)
                    logger.info("备用模型调用成功")
                    return result
                except Exception as e:
                    logger.error(f"备用模型调用失败: {e}")
                    last_error = e

            # 第三层：兜底回复
            logger.warning(f"所有重试失败，返回兜底回复。最后错误: {last_error}")
            return fallback_config.fallback_response

        return wrapper

    return decorator


def with_retry_sync(
    retry_config: Optional[RetryConfig] = None,
    fallback_config: Optional[FallbackConfig] = None,
) -> Callable:
    """
    同步版本的三层重试兜底装饰器

    Args:
        retry_config: 重试配置
        fallback_config: 兜底配置

    Returns:
        装饰器函数
    """
    import time

    if retry_config is None:
        retry_config = RetryConfig()
    if fallback_config is None:
        fallback_config = FallbackConfig()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None

            # 第一层：正常重试
            for attempt in range(retry_config.max_retries):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"第{attempt + 1}次尝试成功")
                    return result

                except retry_config.retryable_errors as e:
                    last_error = e
                    if attempt < retry_config.max_retries - 1:
                        delay = min(
                            retry_config.retry_delay * (retry_config.backoff_factor ** attempt),
                            retry_config.max_delay,
                        )
                        logger.warning(
                            f"第{attempt + 1}次尝试失败: {e}, "
                            f"{delay:.1f}秒后重试..."
                        )
                        time.sleep(delay)
                    else:
                        logger.warning(
                            f"第{attempt + 1}次尝试失败: {e}, "
                            f"尝试降级处理..."
                        )

            # 第二层：降级重试（切换备用模型）
            if fallback_config.fallback_model:
                try:
                    logger.info(f"切换到备用模型: {fallback_config.fallback_model}")
                    kwargs["model"] = fallback_config.fallback_model
                    result = func(*args, **kwargs)
                    logger.info("备用模型调用成功")
                    return result
                except Exception as e:
                    logger.error(f"备用模型调用失败: {e}")
                    last_error = e

            # 第三层：兜底回复
            logger.warning(f"所有重试失败，返回兜底回复。最后错误: {last_error}")
            return fallback_config.fallback_response

        return wrapper

    return decorator


# 预定义的重试配置
LLM_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    retry_delay=1.0,
    backoff_factor=2.0,
    max_delay=10.0,
    retryable_errors=(TimeoutError, ConnectionError, Exception),
)

# 预定义的兜底配置
LLM_FALLBACK_CONFIG = FallbackConfig(
    fallback_response="抱歉，AI服务暂时繁忙，请稍后重试。如有紧急情况，请直接拨打120急救电话。",
    fallback_model=None,  # 可以设置备用模型
)

# 医疗专用兜底回复
MEDICAL_FALLBACK_RESPONSE = (
    "抱歉，系统暂时无法处理您的请求。\n\n"
    "如果您有紧急医疗需求，请：\n"
    "1. 拨打 120 急救电话\n"
    "2. 前往最近的医院急诊科\n\n"
    "系统恢复后，您可以再次尝试咨询。"
)

MEDICAL_FALLBACK_CONFIG = FallbackConfig(
    fallback_response=MEDICAL_FALLBACK_RESPONSE,
)
