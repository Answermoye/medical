"""
MediRouter单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.router_agent import MediRouter, IntentType


@pytest.fixture
def router():
    """创建MediRouter实例"""
    return MediRouter()


def test_router_initialization(router):
    """测试MediRouter初始化"""
    assert router is not None
    assert router.safety_engine is not None


def test_classify_by_keywords_triage(router):
    """测试关键词分类-导诊"""
    test_cases = [
        "我头疼怎么办",
        "胸闷气短看什么科",
        "发烧了应该挂什么科",
        "最近总是失眠",
    ]

    for text in test_cases:
        result = router._classify_by_keywords(text)
        assert result == IntentType.TRIAGE, f"'{text}' should be triage"


def test_classify_by_keywords_report(router):
    """测试关键词分类-报告解读"""
    test_cases = [
        "帮我看看这个化验单",
        "血糖偏高是什么意思",
        "这个报告正常吗",
        "血常规检查结果",
    ]

    for text in test_cases:
        result = router._classify_by_keywords(text)
        assert result == IntentType.REPORT, f"'{text}' should be report"


def test_classify_by_keywords_general(router):
    """测试关键词分类-通用问答"""
    test_cases = [
        "如何保持健康",
        "养生保健方法",
        "健康生活习惯",
    ]

    for text in test_cases:
        result = router._classify_by_keywords(text)
        assert result == IntentType.GENERAL, f"'{text}' should be general"


def test_classify_by_keywords_no_match(router):
    """测试关键词分类-无匹配"""
    result = router._classify_by_keywords("你好")
    assert result is None


def test_get_route_info(router):
    """测试获取路由信息"""
    info = router.get_route_info("我头疼")

    assert "input" in info
    assert "input_length" in info
    assert "keyword_scores" in info
    assert "safety_check" in info
    assert info["keyword_scores"]["triage"] > 0


@pytest.mark.asyncio
async def test_route_emergency(router):
    """测试紧急症状拦截"""
    test_cases = [
        "我胸痛得厉害",
        "呼吸困难",
        "大出血",
    ]

    for text in test_cases:
        result = await router.route(text)
        assert result["blocked"] is True
        assert result["safety_flag"] == "emergency"


@pytest.mark.asyncio
async def test_route_prescription(router):
    """测试处方请求拦截"""
    result = await router.route("帮我开处方")
    assert result["blocked"] is True
    assert result["safety_flag"] == "blocked"


@pytest.mark.asyncio
async def test_route_diagnosis(router):
    """测试确诊请求拦截"""
    result = await router.route("我是不是得了癌症")
    assert result["blocked"] is True
    assert result["safety_flag"] == "blocked"


@pytest.mark.asyncio
async def test_route_chitchat(router):
    """测试闲聊"""
    result = await router.route("你好")
    assert result["blocked"] is False
    assert result["intent"] == IntentType.GENERAL


@pytest.mark.asyncio
async def test_route_with_image(router):
    """测试带图片路由"""
    result = await router.route("帮我看看", has_image=True)
    assert result["blocked"] is False
    assert result["intent"] == IntentType.REPORT


@pytest.mark.asyncio
async def test_route_triage(router):
    """测试导诊路由"""
    with patch.object(router, '_classify_by_llm', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = IntentType.TRIAGE

        result = await router.route("我最近总是头疼")
        assert result["blocked"] is False
        assert result["intent"] == IntentType.TRIAGE


@pytest.mark.asyncio
async def test_route_report(router):
    """测试报告路由"""
    with patch.object(router, '_classify_by_llm', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = IntentType.REPORT

        result = await router.route("帮我看看这个化验单")
        assert result["blocked"] is False
        assert result["intent"] == IntentType.REPORT


@pytest.mark.asyncio
async def test_route_general(router):
    """测试通用路由"""
    with patch.object(router, '_classify_by_keywords', return_value=None), \
         patch.object(router, '_classify_by_llm', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = IntentType.GENERAL

        result = await router.route("什么是高血压")
        assert result["blocked"] is False
        assert result["intent"] == IntentType.GENERAL
