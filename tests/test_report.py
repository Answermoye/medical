"""
ReportAgent单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.report_agent import ReportAgent, ReportState


@pytest.fixture
def report_agent():
    """创建ReportAgent实例"""
    return ReportAgent()


@pytest.fixture
def sample_state():
    """创建示例状态"""
    return ReportState(
        report_id="test-report-001",
        user_id="test-user-001",
        image_path="/uploads/report.jpg",
        session_id="test-session-001",
        ocr_raw_data="",
        parsed_lab_values=[],
        lab_values_with_reference=[],
        abnormal_items=[],
        risk_level="normal",
        relevant_guidelines=[],
        interpretation="",
        pending_review=True,
        review_status="pending",
        doctor_comment="",
        doctor_modified_text="",
        degraded_output=False,
        response="",
        audit_log=[],
    )


def test_report_agent_initialization(report_agent):
    """测试ReportAgent初始化"""
    assert report_agent is not None
    assert report_agent.hitl_timeout_minutes == 60


def test_report_agent_graph_structure(report_agent):
    """测试工作流图结构"""
    assert report_agent.graph is not None


def test_should_query_guidelines_normal(report_agent):
    """测试正常风险等级不检索指南"""
    state = ReportState(
        report_id="test",
        user_id="test",
        image_path="",
        session_id=None,
        ocr_raw_data="",
        parsed_lab_values=[],
        lab_values_with_reference=[],
        abnormal_items=[],
        risk_level="normal",
        relevant_guidelines=[],
        interpretation="",
        pending_review=True,
        review_status="pending",
        doctor_comment="",
        doctor_modified_text="",
        degraded_output=False,
        response="",
        audit_log=[],
    )

    result = report_agent._should_query_guidelines(state)
    assert result == "skip_guidelines"


def test_should_query_guidelines_attention(report_agent):
    """测试关注风险等级检索指南"""
    state = ReportState(
        report_id="test",
        user_id="test",
        image_path="",
        session_id=None,
        ocr_raw_data="",
        parsed_lab_values=[],
        lab_values_with_reference=[],
        abnormal_items=[],
        risk_level="attention",
        relevant_guidelines=[],
        interpretation="",
        pending_review=True,
        review_status="pending",
        doctor_comment="",
        doctor_modified_text="",
        degraded_output=False,
        response="",
        audit_log=[],
    )

    result = report_agent._should_query_guidelines(state)
    assert result == "query_guidelines"


def test_format_interpretation(report_agent):
    """测试格式化解读文本"""
    data = {
        "summary": "总体评估",
        "details": [
            {
                "item_name": "血糖",
                "explanation": "血糖偏高",
                "suggestion": "注意饮食",
            }
        ],
        "recommendations": ["建议1", "建议2"],
        "disclaimer": "仅供参考",
    }

    result = report_agent._format_interpretation(data)

    assert "总体评估" in result
    assert "血糖" in result
    assert "血糖偏高" in result
    assert "建议1" in result
    assert "仅供参考" in result


def test_build_final_response(report_agent):
    """测试构建最终回复"""
    abnormal_items = [
        {
            "item_name": "血糖",
            "value": 7.5,
            "unit": "mmol/L",
            "reference_range": "3.9-6.1",
            "abnormal_type": "high",
        }
    ]

    response = report_agent._build_final_response(
        final_text="测试解读",
        abnormal_items=abnormal_items,
        risk_level="attention",
        doctor_comment="同意",
        review_status="approved",
    )

    assert "报告解读结果" in response
    assert "关注" in response
    assert "血糖" in response
    assert "7.5" in response
    assert "测试解读" in response
    assert "医生批注" in response
    assert "医生审核" in response


@pytest.mark.asyncio
async def test_parse_report_image(report_agent, sample_state):
    """测试OCR识别"""
    mock_response = '{"patient_info": {"name": "张三", "gender": "男", "age": 30}, "lab_items": [{"item_name": "血糖", "result": "7.5", "reference_range": "3.9-6.1", "unit": "mmol/L"}]}'

    with patch("backend.agents.report_agent.llm_factory") as mock_llm:
        mock_llm.invoke = AsyncMock(return_value=mock_response)

        result = await report_agent.parse_report_image(sample_state)

        assert "ocr_raw_data" in result
        assert "parsed_lab_values" in result


@pytest.mark.asyncio
async def test_extract_lab_values(report_agent, sample_state):
    """测试结构化提取"""
    sample_state["parsed_lab_values"] = [
        {"item_name": "血糖", "result": "7.5", "reference_range": "3.9-6.1", "unit": "mmol/L"}
    ]

    mock_response = '''[
        {"item_name": "血糖", "item_name_en": "GLU", "value": 7.5, "unit": "mmol/L", "reference_low": 3.9, "reference_high": 6.1}
    ]'''

    with patch("backend.agents.report_agent.llm_factory") as mock_llm:
        mock_llm.invoke = AsyncMock(return_value=mock_response)

        result = await report_agent.extract_lab_values(sample_state)

        assert "parsed_lab_values" in result
        assert len(result["parsed_lab_values"]) > 0


@pytest.mark.asyncio
async def test_identify_abnormalities_high(report_agent, sample_state):
    """测试识别偏高异常"""
    sample_state["lab_values_with_reference"] = [
        {"item_name": "血糖", "value": 7.5, "unit": "mmol/L", "reference_low": 3.9, "reference_high": 6.1}
    ]

    result = await report_agent.identify_abnormalities(sample_state)

    assert "abnormal_items" in result
    assert len(result["abnormal_items"]) > 0
    assert result["abnormal_items"][0]["abnormal_type"] == "high"


@pytest.mark.asyncio
async def test_identify_abnormalities_low(report_agent, sample_state):
    """测试识别偏低异常"""
    sample_state["lab_values_with_reference"] = [
        {"item_name": "血红蛋白", "value": 100, "unit": "g/L", "reference_low": 120, "reference_high": 160}
    ]

    result = await report_agent.identify_abnormalities(sample_state)

    assert "abnormal_items" in result
    assert len(result["abnormal_items"]) > 0
    assert result["abnormal_items"][0]["abnormal_type"] == "low"


@pytest.mark.asyncio
async def test_identify_abnormalities_normal(report_agent, sample_state):
    """测试正常值"""
    sample_state["lab_values_with_reference"] = [
        {"item_name": "血糖", "value": 5.0, "unit": "mmol/L", "reference_low": 3.9, "reference_high": 6.1}
    ]

    result = await report_agent.identify_abnormalities(sample_state)

    assert "abnormal_items" in result
    assert len(result["abnormal_items"]) == 0


@pytest.mark.asyncio
async def test_analyze_risk_level(report_agent, sample_state):
    """测试风险等级分析"""
    sample_state["abnormal_items"] = [
        {"item_name": "血糖", "value": 7.5, "abnormal_type": "high"}
    ]

    mock_response = '{"risk_level": "attention", "reason": "血糖偏高"}'

    with patch("backend.agents.report_agent.llm_factory") as mock_llm:
        mock_llm.invoke = AsyncMock(return_value=mock_response)

        result = await report_agent.analyze_risk_level(sample_state)

        assert "risk_level" in result
        assert result["risk_level"] in ["normal", "attention", "see_doctor"]


@pytest.mark.asyncio
async def test_generate_interpretation(report_agent, sample_state):
    """测试生成解读"""
    sample_state["abnormal_items"] = [
        {"item_name": "血糖", "value": 7.5, "abnormal_type": "high", "meaning": "可能提示糖尿病"}
    ]
    sample_state["risk_level"] = "attention"

    mock_response = '''{
        "summary": "血糖偏高",
        "details": [
            {"item_name": "血糖", "explanation": "您的血糖值偏高", "suggestion": "注意饮食控制"}
        ],
        "recommendations": ["建议复查血糖"],
        "disclaimer": "仅供参考"
    }'''

    with patch("backend.agents.report_agent.llm_factory") as mock_llm:
        mock_llm.invoke = AsyncMock(return_value=mock_response)

        result = await report_agent.generate_interpretation(sample_state)

        assert "interpretation" in result
        assert len(result["interpretation"]) > 0


@pytest.mark.asyncio
async def test_apply_doctor_decision_approved(report_agent, sample_state):
    """测试医生批准"""
    sample_state["interpretation"] = "测试解读"
    sample_state["review_status"] = "approved"
    sample_state["doctor_comment"] = "同意"
    sample_state["abnormal_items"] = [
        {"item_name": "血糖", "value": 7.5, "unit": "mmol/L", "reference_range": "3.9-6.1", "abnormal_type": "high"}
    ]

    result = await report_agent.apply_doctor_decision(sample_state)

    assert "response" in result
    assert "测试解读" in result["response"]
    assert "医生审核" in result["response"]


@pytest.mark.asyncio
async def test_apply_doctor_decision_modified(report_agent, sample_state):
    """测试医生修改"""
    sample_state["interpretation"] = "AI解读"
    sample_state["review_status"] = "modified"
    sample_state["doctor_modified_text"] = "医生修改后的解读"
    sample_state["abnormal_items"] = []

    result = await report_agent.apply_doctor_decision(sample_state)

    assert "response" in result
    assert "医生修改后的解读" in result["response"]
    assert "医生修改" in result["response"]


@pytest.mark.asyncio
async def test_apply_doctor_decision_rejected(report_agent, sample_state):
    """测试医生驳回"""
    sample_state["interpretation"] = "AI解读"
    sample_state["review_status"] = "rejected"
    sample_state["abnormal_items"] = []

    result = await report_agent.apply_doctor_decision(sample_state)

    assert "response" in result
    assert "专业咨询" in result["response"]
