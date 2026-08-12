"""
Orchestrator单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.core.orchestrator import Orchestrator
from backend.agents.router_agent import IntentType


@pytest.fixture
def orchestrator():
    """创建Orchestrator实例"""
    return Orchestrator()


def test_orchestrator_initialization(orchestrator):
    """测试Orchestrator初始化"""
    assert orchestrator is not None
    assert orchestrator.router is not None
    assert orchestrator.triage_agent is not None
    assert orchestrator.report_agent is not None
    assert orchestrator.general_agent is not None


def test_get_agent_info(orchestrator):
    """测试获取智能体信息"""
    info = orchestrator.get_agent_info()

    assert "router" in info
    assert "triage" in info
    assert "report" in info
    assert "general" in info


@pytest.mark.asyncio
async def test_process_blocked(orchestrator):
    """测试安全拦截"""
    with patch.object(orchestrator.router, 'route', new_callable=AsyncMock) as mock_route:
        mock_route.return_value = {
            "intent": None,
            "safety_flag": "emergency",
            "blocked": True,
            "response": "紧急提醒...",
            "reason": "emergency",
        }

        result = await orchestrator.process("我胸痛", "user1")

        assert result["blocked"] is True
        assert "紧急提醒" in result["response"]


@pytest.mark.asyncio
async def test_process_triage(orchestrator):
    """测试导诊处理"""
    with patch.object(orchestrator.router, 'route', new_callable=AsyncMock) as mock_route, \
         patch.object(orchestrator.triage_agent, 'process', new_callable=AsyncMock) as mock_triage:
        mock_route.return_value = {
            "intent": IntentType.TRIAGE,
            "safety_flag": "safe",
            "blocked": False,
            "response": None,
            "reason": "keyword_match",
        }

        mock_triage.return_value = {
            "response": "导诊结果...",
            "symptoms": ["头痛"],
            "recommended_departments": [{"department": "神经内科"}],
            "followup_rounds": 0,
        }

        result = await orchestrator.process("我头疼", "user1")

        assert result["intent"] == IntentType.TRIAGE
        assert result["blocked"] is False
        assert "导诊结果" in result["response"]


@pytest.mark.asyncio
async def test_process_report_no_image(orchestrator):
    """测试报告处理-无图片"""
    with patch.object(orchestrator.router, 'route', new_callable=AsyncMock) as mock_route:
        mock_route.return_value = {
            "intent": IntentType.REPORT,
            "safety_flag": "safe",
            "blocked": False,
            "response": None,
            "reason": "keyword_match",
        }

        result = await orchestrator.process("帮我看看报告", "user1")

        assert result["intent"] == IntentType.REPORT
        assert result["blocked"] is False
        assert "上传" in result["response"]


@pytest.mark.asyncio
async def test_process_report_with_image(orchestrator):
    """测试报告处理-有图片"""
    with patch.object(orchestrator.router, 'route', new_callable=AsyncMock) as mock_route, \
         patch.object(orchestrator.report_agent, 'process', new_callable=AsyncMock) as mock_report:
        mock_route.return_value = {
            "intent": IntentType.REPORT,
            "safety_flag": "safe",
            "blocked": False,
            "response": None,
            "reason": "image_detected",
        }

        mock_report.return_value = {
            "response": "报告解读结果...",
            "risk_level": "attention",
            "abnormal_items": [{"item_name": "血糖"}],
        }

        result = await orchestrator.process("帮我看看报告", "user1", image_path="/uploads/report.jpg")

        assert result["intent"] == IntentType.REPORT
        assert result["blocked"] is False
        assert "报告解读" in result["response"]


@pytest.mark.asyncio
async def test_process_general(orchestrator):
    """测试通用问答处理"""
    with patch.object(orchestrator.router, 'route', new_callable=AsyncMock) as mock_route, \
         patch.object(orchestrator.general_agent, 'process', new_callable=AsyncMock) as mock_general:
        mock_route.return_value = {
            "intent": IntentType.GENERAL,
            "safety_flag": "safe",
            "blocked": False,
            "response": None,
            "reason": "keyword_match",
        }

        mock_general.return_value = "高血压是指..."

        result = await orchestrator.process("什么是高血压", "user1")

        assert result["intent"] == IntentType.GENERAL
        assert result["blocked"] is False
        assert "高血压" in result["response"]
