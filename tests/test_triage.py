"""
TriageAgent单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.triage_agent import TriageAgent, TriageState


@pytest.fixture
def triage_agent():
    """创建TriageAgent实例"""
    return TriageAgent()


@pytest.fixture
def sample_state():
    """创建示例状态"""
    return TriageState(
        user_input="我最近总是头痛，已经持续3天了",
        conversation_history=[],
        symptoms=[],
        symptom_details={},
        info_completeness=0.0,
        recommended_departments=[],
        followup_questions=[],
        followup_rounds=0,
        advice="",
        response="",
    )


def test_triage_agent_initialization(triage_agent):
    """测试TriageAgent初始化"""
    assert triage_agent is not None
    assert triage_agent.max_followup_rounds == 3
    assert triage_agent.min_info_completeness == 0.6


def test_triage_agent_graph_structure(triage_agent):
    """测试工作流图结构"""
    assert triage_agent.graph is not None


def test_should_ask_followup_low_completeness(triage_agent):
    """测试低完整性时应该追问"""
    state = TriageState(
        user_input="我头疼",
        conversation_history=[],
        symptoms=["头痛"],
        symptom_details={},
        info_completeness=0.3,
        recommended_departments=[],
        followup_questions=[],
        followup_rounds=0,
        advice="",
        response="",
    )

    result = triage_agent._should_ask_followup(state)
    assert result == "ask_followup"


def test_should_ask_followup_high_completeness(triage_agent):
    """测试高完整性时应该推荐"""
    state = TriageState(
        user_input="我头疼",
        conversation_history=[],
        symptoms=["头痛"],
        symptom_details={"duration": "3天", "severity": "中等"},
        info_completeness=0.8,
        recommended_departments=[{"department": "神经内科"}],
        followup_questions=[],
        followup_rounds=0,
        advice="",
        response="",
    )

    result = triage_agent._should_ask_followup(state)
    assert result == "recommend"


def test_should_ask_followup_max_rounds(triage_agent):
    """测试达到最大追问轮数时应该推荐"""
    state = TriageState(
        user_input="我头疼",
        conversation_history=[],
        symptoms=["头痛"],
        symptom_details={},
        info_completeness=0.3,
        recommended_departments=[],
        followup_questions=[],
        followup_rounds=3,
        advice="",
        response="",
    )

    result = triage_agent._should_ask_followup(state)
    assert result == "recommend"


def test_build_response(triage_agent):
    """测试构建回复"""
    symptoms = ["头痛", "发烧"]
    departments = [
        {"department": "神经内科", "reason": "头痛相关"},
        {"department": "内科", "reason": "发烧相关"},
    ]
    advice = {
        "visit_advice": "建议先到神经内科就诊",
        "examination_advice": "可能需要做头部CT",
        "precautions": "就医前注意记录症状",
    }

    response = triage_agent._build_response(symptoms, departments, advice)

    assert "导诊结果" in response
    assert "头痛" in response
    assert "发烧" in response
    assert "神经内科" in response
    assert "内科" in response
    assert "就医建议" in response
    assert "可能检查" in response
    assert "注意事项" in response
    assert "免责声明" in response or "仅供参考" in response


@pytest.mark.asyncio
async def test_parse_symptom(triage_agent, sample_state):
    """测试症状解析"""
    mock_response = '["头痛", "头晕"]'

    with patch("backend.agents.triage_agent.llm_factory") as mock_llm:
        mock_llm.invoke_with_messages = AsyncMock(return_value=mock_response)

        result = await triage_agent.parse_symptom(sample_state)

        assert "symptoms" in result
        assert "头痛" in result["symptoms"]
        assert "头晕" in result["symptoms"]


@pytest.mark.asyncio
async def test_extract_entities(triage_agent, sample_state):
    """测试实体提取"""
    sample_state["symptoms"] = ["头痛"]
    mock_response = '{"duration": "3天", "severity": "中等", "accompanying_symptoms": ["头晕"]}'

    with patch("backend.agents.triage_agent.llm_factory") as mock_llm:
        mock_llm.invoke_with_messages = AsyncMock(return_value=mock_response)

        result = await triage_agent.extract_entities(sample_state)

        assert "symptom_details" in result
        assert result["symptom_details"]["duration"] == "3天"
        assert result["symptom_details"]["severity"] == "中等"


@pytest.mark.asyncio
async def test_query_department_kb(triage_agent, sample_state):
    """测试科室知识库查询"""
    sample_state["symptoms"] = ["头痛"]
    sample_state["symptom_details"] = {"duration": "3天", "severity": "中等"}

    mock_embedding = [0.1] * 1024
    mock_search_results = [
        {"department": "神经内科", "score": 0.9, "description": "神经系统疾病"},
        {"department": "眼科", "score": 0.7, "description": "眼部疾病"},
    ]

    with patch("backend.agents.triage_agent.embedder") as mock_embedder, \
         patch("backend.agents.triage_agent.kb_client") as mock_kb:
        mock_embedder.encode_single = MagicMock(return_value=mock_embedding)
        mock_kb.search_symptoms = MagicMock(return_value=mock_search_results)

        result = await triage_agent.query_department_kb(sample_state)

        assert "recommended_departments" in result
        assert len(result["recommended_departments"]) > 0


def test_check_info_completeness(triage_agent, sample_state):
    """测试信息完整性检查"""
    # 有症状
    sample_state["symptoms"] = ["头痛"]
    sample_state["symptom_details"] = {}
    sample_state["recommended_departments"] = []

    result = triage_agent.check_info_completeness(sample_state)
    assert result["info_completeness"] >= 0.4

    # 有症状和持续时间
    sample_state["symptom_details"] = {"duration": "3天"}
    result = triage_agent.check_info_completeness(sample_state)
    assert result["info_completeness"] >= 0.6

    # 有症状、持续时间和严重程度
    sample_state["symptom_details"] = {"duration": "3天", "severity": "中等"}
    result = triage_agent.check_info_completeness(sample_state)
    assert result["info_completeness"] >= 0.8


@pytest.mark.asyncio
async def test_recommend_department(triage_agent, sample_state):
    """测试科室推荐"""
    sample_state["symptoms"] = ["头痛"]
    sample_state["symptom_details"] = {"duration": "3天", "severity": "中等"}
    sample_state["recommended_departments"] = []

    mock_response = '''[
        {"department": "神经内科", "reason": "头痛可能与神经系统相关"},
        {"department": "眼科", "reason": "如果伴有视力问题"}
    ]'''

    with patch("backend.agents.triage_agent.llm_factory") as mock_llm:
        mock_llm.invoke_with_messages = AsyncMock(return_value=mock_response)

        result = await triage_agent.recommend_department(sample_state)

        assert "recommended_departments" in result
        assert len(result["recommended_departments"]) <= 3


@pytest.mark.asyncio
async def test_generate_advice(triage_agent, sample_state):
    """测试生成就医建议"""
    sample_state["symptoms"] = ["头痛"]
    sample_state["symptom_details"] = {"duration": "3天", "severity": "中等"}
    sample_state["recommended_departments"] = [
        {"department": "神经内科", "reason": "头痛相关"},
    ]

    mock_response = '''{
        "visit_advice": "建议到神经内科就诊",
        "examination_advice": "可能需要做头部CT",
        "precautions": "就医前注意记录症状发作时间"
    }'''

    with patch("backend.agents.triage_agent.llm_factory") as mock_llm:
        mock_llm.invoke_with_messages = AsyncMock(return_value=mock_response)

        result = await triage_agent.generate_advice(sample_state)

        assert "advice" in result
        assert "response" in result
        assert "神经内科" in result["response"]
