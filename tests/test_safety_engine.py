"""
安全引擎单元测试
"""

import pytest

from backend.core.safety_engine import SafetyEngine, SafetyLevel


@pytest.fixture
def safety_engine():
    """创建SafetyEngine实例"""
    return SafetyEngine()


def test_emergency_symptom_detection(safety_engine):
    """测试紧急症状检测"""
    test_cases = [
        ("我胸痛得厉害", True),
        ("呼吸困难，喘不过气", True),
        ("大出血止不住", True),
        ("我昏迷了", True),
        ("我头疼", False),
        ("我感冒了", False),
    ]

    for text, expected in test_cases:
        result = safety_engine.check(text)
        if expected:
            assert result["level"] == SafetyLevel.EMERGENCY, f"'{text}' should be emergency"
            assert result["blocked"] is True
        else:
            assert result["level"] != SafetyLevel.EMERGENCY, f"'{text}' should not be emergency"


def test_prescription_request_detection(safety_engine):
    """测试处方请求检测"""
    test_cases = [
        ("帮我开处方", True),
        ("开点抗生素", True),
        ("给我开药", True),
        ("我想看病", False),
        ("我头疼怎么办", False),
    ]

    for text, expected in test_cases:
        result = safety_engine.check(text)
        if expected:
            assert result["level"] == SafetyLevel.BLOCKED, f"'{text}' should be blocked"
            assert result["blocked"] is True
        else:
            assert result["level"] != SafetyLevel.BLOCKED, f"'{text}' should not be blocked"


def test_diagnosis_request_detection(safety_engine):
    """测试确诊请求检测"""
    test_cases = [
        ("我是不是得了癌症", True),
        ("我确诊了吗", True),
        ("我有病吗", True),
        ("我头疼", False),
        ("我发烧了", False),
    ]

    for text, expected in test_cases:
        result = safety_engine.check(text)
        if expected:
            assert result["level"] == SafetyLevel.BLOCKED, f"'{text}' should be blocked"
            assert result["blocked"] is True
        else:
            assert result["level"] != SafetyLevel.BLOCKED, f"'{text}' should not be blocked"


def test_psychological_crisis_detection(safety_engine):
    """测试心理危机检测"""
    test_cases = [
        ("我想死", True),
        ("不想活了", True),
        ("我有自杀倾向", True),
        ("我心情不好", False),
        ("我压力大", False),
    ]

    for text, expected in test_cases:
        result = safety_engine.check(text)
        if expected:
            assert result["level"] == SafetyLevel.EMERGENCY, f"'{text}' should be emergency"
            assert result["blocked"] is True
        else:
            assert result["level"] != SafetyLevel.EMERGENCY, f"'{text}' should not be emergency"


def test_chitchat_detection(safety_engine):
    """测试闲聊检测"""
    test_cases = [
        ("你好", True),
        ("嗨", True),
        ("你是谁", True),
        ("我头疼怎么办", False),
        ("我想咨询一下医疗问题", False),
    ]

    for text, expected in test_cases:
        result = safety_engine.check(text)
        if expected:
            assert result.get("is_chitchat") is True, f"'{text}' should be chitchat"
        else:
            assert result.get("is_chitchat") is not True, f"'{text}' should not be chitchat"


def test_safe_input(safety_engine):
    """测试安全输入"""
    test_cases = [
        "我头疼怎么办",
        "我发烧了，38度",
        "我最近总是失眠",
        "我胃不舒服",
    ]

    for text in test_cases:
        result = safety_engine.check(text)
        assert result["level"] == SafetyLevel.SAFE, f"'{text}' should be safe"
        assert result["blocked"] is False


def test_emergency_response_content(safety_engine):
    """测试紧急回复内容"""
    result = safety_engine.check("我胸痛")
    assert "120" in result["response"]
    assert "急救" in result["response"]


def test_prescription_response_content(safety_engine):
    """测试处方回复内容"""
    result = safety_engine.check("帮我开处方")
    assert "处方" in result["response"]
    assert "医生" in result["response"]


def test_diagnosis_response_content(safety_engine):
    """测试确诊回复内容"""
    result = safety_engine.check("我是不是得了癌症")
    assert "诊断" in result["response"] or "确诊" in result["response"]


def test_psychological_crisis_response_content(safety_engine):
    """测试心理危机回复内容"""
    result = safety_engine.check("我想死")
    assert "热线" in result["response"]
    assert "心理" in result["response"]


def test_safety_report(safety_engine):
    """测试安全检查报告"""
    report = safety_engine.get_safety_report("我胸痛")
    assert "input" in report
    assert "level" in report
    assert "blocked" in report
    assert "reason" in report
    assert report["has_emergency_keyword"] is True
