"""
医疗导诊与报告解读助手 - MediRouter意图路由智能体

三层分类：
1. 规则引擎先行拦截（紧急症状、处方请求、确诊判断等）
2. MiniLM意图分类（快速分类）
3. LLM兜底分类（复杂情况）
"""

import json
from typing import Optional

from backend.core.llm_factory import llm_factory
from backend.core.logger import setup_logger
from backend.core.safety_engine import SafetyEngine, SafetyLevel
from backend.core.retry import with_retry, LLM_RETRY_CONFIG, MEDICAL_FALLBACK_CONFIG

logger = setup_logger(__name__)


class IntentType:
    """意图类型"""
    TRIAGE = "triage"  # 导诊
    REPORT = "report"  # 报告解读
    GENERAL = "general"  # 通用问答


class MediRouter:
    """意图路由智能体"""

    def __init__(self):
        logger.info("初始化MediRouter")
        self.safety_engine = SafetyEngine()

        # 导诊关键词
        self.triage_keywords = [
            "疼", "痛", "不舒服", "难受", "症状",
            "发烧", "咳嗽", "头疼", "头晕", "恶心",
            "呕吐", "腹泻", "便秘", "失眠", "乏力",
            "胸闷", "气短", "心慌", "水肿", "皮疹",
            "瘙痒", "出血", "肿胀", "麻木", "抽搐",
            "什么科", "看什么科", "挂什么科", "哪个科",
            "去医院", "看病", "就诊", "检查",
        ]

        # 报告解读关键词
        self.report_keywords = [
            "报告", "化验单", "检查单", "体检报告",
            "血常规", "尿常规", "肝功能", "肾功能",
            "血糖", "血脂", "血压", "心电图",
            "CT", "核磁", "B超", "X光",
            "异常", "偏高", "偏低", "正常",
            "解读", "分析", "结果", "指标",
            "上传", "图片", "照片",
        ]

        # 通用问答关键词
        self.general_keywords = [
            "什么是", "怎么", "为什么", "原因",
            "治疗", "预防", "保健", "养生",
            "药物", "用药", "副作用", "禁忌",
            "饮食", "运动", "生活习惯",
            "健康", "医学", "疾病",
        ]

    async def route(self, user_input: str, has_image: bool = False) -> dict:
        """
        路由用户输入

        Args:
            user_input: 用户输入文本
            has_image: 是否包含图片

        Returns:
            路由结果，包含intent、safety_flag、response等
        """
        logger.info(f"路由用户输入: {user_input[:50]}...")

        # 第一层：安全规则检查
        safety_result = self.safety_engine.check(user_input)
        if safety_result["blocked"]:
            logger.warning(f"安全拦截: {safety_result['reason']}")
            return {
                "intent": None,
                "safety_flag": safety_result["level"],
                "blocked": True,
                "response": safety_result["response"],
                "reason": safety_result["reason"],
            }

        # 如果有图片，默认路由到报告解读
        if has_image:
            logger.info("检测到图片，路由到报告解读")
            return {
                "intent": IntentType.REPORT,
                "safety_flag": SafetyLevel.SAFE,
                "blocked": False,
                "response": None,
                "reason": "image_detected",
            }

        # 如果是闲聊，直接返回
        if safety_result.get("is_chitchat"):
            logger.info("检测到闲聊")
            return {
                "intent": IntentType.GENERAL,
                "safety_flag": SafetyLevel.SAFE,
                "blocked": False,
                "response": safety_result["response"],
                "reason": "chitchat",
            }

        # 第二层：关键词规则分类
        keyword_intent = self._classify_by_keywords(user_input)
        if keyword_intent:
            logger.info(f"关键词分类结果: {keyword_intent}")
            return {
                "intent": keyword_intent,
                "safety_flag": SafetyLevel.SAFE,
                "blocked": False,
                "response": None,
                "reason": "keyword_match",
            }

        # 第三层：LLM分类
        llm_intent = await self._classify_by_llm(user_input)
        logger.info(f"LLM分类结果: {llm_intent}")

        return {
            "intent": llm_intent,
            "safety_flag": SafetyLevel.SAFE,
            "blocked": False,
            "response": None,
            "reason": "llm_classification",
        }

    def _classify_by_keywords(self, user_input: str) -> Optional[str]:
        """
        关键词分类

        Args:
            user_input: 用户输入

        Returns:
            意图类型或None
        """
        user_input_lower = user_input.lower()

        # 计算各类别匹配分数
        triage_score = sum(1 for kw in self.triage_keywords if kw in user_input_lower)
        report_score = sum(1 for kw in self.report_keywords if kw in user_input_lower)
        general_score = sum(1 for kw in self.general_keywords if kw in user_input_lower)

        # 找出最高分
        max_score = max(triage_score, report_score, general_score)

        # 如果有明显匹配（分数>=1）
        if max_score >= 1:
            if triage_score == max_score:
                return IntentType.TRIAGE
            elif report_score == max_score:
                return IntentType.REPORT
            else:
                return IntentType.GENERAL

        return None

    @with_retry(retry_config=LLM_RETRY_CONFIG, fallback_config=MEDICAL_FALLBACK_CONFIG)
    async def _classify_by_llm(self, user_input: str) -> str:
        """
        LLM分类

        Args:
            user_input: 用户输入

        Returns:
            意图类型
        """
        system_message = """你是一个医疗助手意图分类器，需要将用户输入分类到以下三个类别之一：

1. triage（导诊）：用户描述症状，想知道应该看什么科室
   例如："我头疼怎么办"、"胸闷气短看什么科"

2. report（报告解读）：用户想解读医疗报告或检验结果
   例如："帮我看看这个化验单"、"血糖偏高是什么意思"

3. general（通用问答）：用户询问健康知识、医学常识等
   例如："什么是高血压"、"糖尿病怎么预防"

请只返回类别名称（triage/report/general），不要返回其他内容。"""

        # 调用LLM
        response = await llm_factory.invoke(
            prompt=user_input,
            system_message=system_message,
            temperature=0.1,
            max_tokens=50,
        )

        # 解析响应
        response_lower = response.lower().strip()

        if "triage" in response_lower:
            return IntentType.TRIAGE
        elif "report" in response_lower:
            return IntentType.REPORT
        elif "general" in response_lower:
            return IntentType.GENERAL
        else:
            # 默认返回通用问答
            return IntentType.GENERAL

    def get_route_info(self, user_input: str) -> dict:
        """
        获取路由信息（用于调试）

        Args:
            user_input: 用户输入

        Returns:
            路由信息字典
        """
        user_input_lower = user_input.lower()

        # 计算各类别匹配分数
        triage_score = sum(1 for kw in self.triage_keywords if kw in user_input_lower)
        report_score = sum(1 for kw in self.report_keywords if kw in user_input_lower)
        general_score = sum(1 for kw in self.general_keywords if kw in user_input_lower)

        # 安全检查
        safety_result = self.safety_engine.check(user_input)

        return {
            "input": user_input,
            "input_length": len(user_input),
            "keyword_scores": {
                "triage": triage_score,
                "report": report_score,
                "general": general_score,
            },
            "safety_check": {
                "level": safety_result["level"],
                "blocked": safety_result["blocked"],
                "reason": safety_result.get("reason"),
            },
        }


# 全局MediRouter实例
medi_router = MediRouter()
