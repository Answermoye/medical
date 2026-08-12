"""
医疗导诊与报告解读助手 - 安全规则引擎

实现紧急症状拦截、处方拒绝、确诊拒绝等安全规则
"""

import re
from typing import Optional

from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class SafetyLevel:
    """安全等级"""
    SAFE = "safe"
    EMERGENCY = "emergency"
    BLOCKED = "blocked"
    WARNING = "warning"


class SafetyEngine:
    """安全规则引擎"""

    def __init__(self):
        logger.info("初始化SafetyEngine")
        self._init_rules()

    def _init_rules(self) -> None:
        """初始化安全规则"""

        # 紧急症状关键词
        self.emergency_keywords = [
            "胸痛", "胸口疼", "胸闷", "呼吸困难", "喘不过气",
            "大出血", "出血不止", "吐血", "便血",
            "昏迷", "晕倒", "失去意识",
            "中风", "偏瘫", "口齿不清",
            "心梗", "心肌梗死", "心脏骤停",
            "过敏性休克", "休克",
            "高热不退", "高烧不退",
            "剧烈头痛", "突发头痛",
            "视力突然模糊", "突然看不见",
            "剧烈腹痛", "腹部剧痛",
            "自杀", "自残",
        ]

        # 处方相关关键词
        self.prescription_keywords = [
            "开处方", "开药", "开药方",
            "给我开", "帮我开", "请开",
            "处方药", "抗生素",
            "剂量", "用量", "用法",
            "一天几次", "一次几片",
        ]

        # 确诊相关关键词
        self.diagnosis_keywords = [
            "我是不是得了", "我得了", "我确诊",
            "是不是癌症", "是不是肿瘤",
            "是不是艾滋病", "是不是白血病",
            "确诊了吗", "诊断结果",
            "我有病吗", "我生病了吗",
        ]

        # 精神/心理危机关键词
        self.psychological_crisis_keywords = [
            "想死", "不想活", "活不下去",
            "自杀", "自残", "割腕",
            "跳楼", "跳河",
            "遗书", "遗言",
            "没有希望", "活着没意思",
        ]

        # 闲聊关键词
        self.chitchat_keywords = [
            "你好", "嗨", "哈喽", "hello", "hi",
            "在吗", "在不在",
            "你是谁", "你叫什么",
            "今天天气", "天气怎么样",
            "谢谢", "感谢",
            "再见", "拜拜",
        ]

        # 兜底回复模板
        self.emergency_response = (
            "⚠️ 紧急提醒：您描述的症状可能需要紧急医疗处理。\n\n"
            "**请立即拨打 120 急救电话或前往最近的急诊科就诊。**\n\n"
            "在等待救护车期间：\n"
            "1. 保持冷静，不要惊慌\n"
            "2. 保持呼吸道通畅\n"
            "3. 不要随意移动患者\n"
            "4. 记录症状发生时间和变化\n\n"
            "生命安全第一，请尽快寻求专业医疗帮助！"
        )

        self.prescription_response = (
            "抱歉，我无法为您开具处方或提供用药建议。\n\n"
            "处方药需要由执业医师根据您的具体情况开具。\n\n"
            "建议您：\n"
            "1. 前往医院就诊\n"
            "2. 由医生进行诊断和开药\n"
            "3. 按医嘱用药\n\n"
            "请不要自行购买和使用处方药，以免造成健康风险。"
        )

        self.diagnosis_response = (
            "抱歉，我无法为您进行确诊或诊断。\n\n"
            "作为AI助手，我只能提供健康咨询和就医建议，不能替代医生进行诊断。\n\n"
            "建议您：\n"
            "1. 前往医院进行专业检查\n"
            "2. 由医生根据检查结果进行诊断\n"
            "3. 遵医嘱进行治疗\n\n"
            "如果您感到担忧，建议尽早预约医生就诊。"
        )

        self.psychological_crisis_response = (
            "❤️ 我听到您现在的痛苦，您并不孤单。\n\n"
            "**全国24小时心理援助热线：**\n"
            "- 希望24热线：400-161-9995\n"
            "- 北京心理危机研究与干预中心：010-82951332\n"
            "- 生命热线：400-821-1215\n\n"
            "如果您或身边的人正处于危险中，请立即拨打 110 或 120。\n\n"
            "您的生命很重要，请寻求专业帮助。"
        )

        self.chitchat_response = (
            "您好！我是医疗导诊与报告解读助手。\n\n"
            "我可以为您提供以下服务：\n"
            "1. **导诊服务** - 根据症状推荐就诊科室\n"
            "2. **报告解读** - 帮助解读检验报告\n"
            "3. **健康咨询** - 回答健康相关问题\n\n"
            "请问有什么可以帮助您的吗？"
        )

    def check(self, user_input: str) -> dict:
        """
        检查用户输入的安全性

        Args:
            user_input: 用户输入文本

        Returns:
            安全检查结果，包含level、blocked、response
        """
        user_input_lower = user_input.lower().strip()

        # 检查紧急症状
        if self._check_emergency(user_input_lower):
            logger.warning(f"检测到紧急症状: {user_input[:50]}...")
            return {
                "level": SafetyLevel.EMERGENCY,
                "blocked": True,
                "response": self.emergency_response,
                "reason": "emergency_symptom",
            }

        # 检查心理危机
        if self._check_psychological_crisis(user_input_lower):
            logger.warning(f"检测到心理危机: {user_input[:50]}...")
            return {
                "level": SafetyLevel.EMERGENCY,
                "blocked": True,
                "response": self.psychological_crisis_response,
                "reason": "psychological_crisis",
            }

        # 检查处方请求
        if self._check_prescription(user_input_lower):
            logger.info(f"检测到处方请求: {user_input[:50]}...")
            return {
                "level": SafetyLevel.BLOCKED,
                "blocked": True,
                "response": self.prescription_response,
                "reason": "prescription_request",
            }

        # 检查确诊请求
        if self._check_diagnosis(user_input_lower):
            logger.info(f"检测到确诊请求: {user_input[:50]}...")
            return {
                "level": SafetyLevel.BLOCKED,
                "blocked": True,
                "response": self.diagnosis_response,
                "reason": "diagnosis_request",
            }

        # 检查闲聊
        if self._check_chitchat(user_input_lower):
            logger.debug(f"检测到闲聊: {user_input[:50]}...")
            return {
                "level": SafetyLevel.SAFE,
                "blocked": False,
                "response": self.chitchat_response,
                "reason": "chitchat",
                "is_chitchat": True,
            }

        # 安全
        return {
            "level": SafetyLevel.SAFE,
            "blocked": False,
            "response": None,
            "reason": None,
        }

    def _check_emergency(self, text: str) -> bool:
        """检查紧急症状"""
        for keyword in self.emergency_keywords:
            if keyword in text:
                return True
        return False

    def _check_prescription(self, text: str) -> bool:
        """检查处方请求"""
        for keyword in self.prescription_keywords:
            if keyword in text:
                return True
        return False

    def _check_diagnosis(self, text: str) -> bool:
        """检查确诊请求"""
        for keyword in self.diagnosis_keywords:
            if keyword in text:
                return True
        return False

    def _check_psychological_crisis(self, text: str) -> bool:
        """检查心理危机"""
        for keyword in self.psychological_crisis_keywords:
            if keyword in text:
                return True
        return False

    def _check_chitchat(self, text: str) -> bool:
        """检查闲聊"""
        # 只有当输入很短时才认为是闲聊
        if len(text) > 20:
            return False

        for keyword in self.chitchat_keywords:
            if keyword in text:
                return True
        return False

    def get_safety_report(self, user_input: str) -> dict:
        """
        获取详细的安全检查报告

        Args:
            user_input: 用户输入

        Returns:
            安全检查报告
        """
        result = self.check(user_input)

        return {
            "input": user_input,
            "input_length": len(user_input),
            "level": result["level"],
            "blocked": result["blocked"],
            "reason": result.get("reason"),
            "has_emergency_keyword": self._check_emergency(user_input.lower()),
            "has_prescription_keyword": self._check_prescription(user_input.lower()),
            "has_diagnosis_keyword": self._check_diagnosis(user_input.lower()),
            "has_psychological_crisis_keyword": self._check_psychological_crisis(user_input.lower()),
            "is_chitchat": result.get("is_chitchat", False),
        }


# 全局SafetyEngine实例
safety_engine = SafetyEngine()
