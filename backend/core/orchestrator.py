"""
医疗导诊与报告解读助手 - 多智能体编排器

编排MediRouter、TriageAgent、ReportAgent、GeneralAgent
"""

from typing import Any, Optional

from backend.agents.router_agent import MediRouter, IntentType
from backend.agents.triage_agent import TriageAgent, TriageState
from backend.agents.report_agent import ReportAgent, ReportState
from backend.agents.general_agent import GeneralAgent
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class Orchestrator:
    """多智能体编排器"""

    def __init__(self):
        logger.info("初始化Orchestrator")
        self.router = MediRouter()
        self.triage_agent = TriageAgent()
        self.report_agent = ReportAgent()
        self.general_agent = GeneralAgent()

    async def process(
        self,
        user_input: str,
        user_id: str,
        session_id: Optional[str] = None,
        image_path: Optional[str] = None,
        conversation_history: Optional[list] = None,
        state: Optional[dict] = None,
    ) -> dict:
        """
        处理用户请求

        Args:
            user_input: 用户输入
            user_id: 用户ID
            session_id: 会话ID
            image_path: 图片路径
            conversation_history: 对话历史
            state: 当前状态（用于追问场景）

        Returns:
            处理结果
        """
        logger.info(f"处理用户请求: {user_input[:50]}...")

        # 检查是否有图片
        has_image = image_path is not None

        # 路由
        route_result = await self.router.route(user_input, has_image)

        # 如果被安全拦截
        if route_result["blocked"]:
            logger.warning(f"请求被安全拦截: {route_result['reason']}")
            return {
                "intent": None,
                "safety_flag": route_result["safety_flag"],
                "blocked": True,
                "response": route_result["response"],
                "reason": route_result["reason"],
            }

        intent = route_result["intent"]
        logger.info(f"路由结果: {intent}")

        # 根据意图分发到对应的智能体
        if intent == IntentType.TRIAGE:
            result = await self._handle_triage(
                user_input=user_input,
                user_id=user_id,
                session_id=session_id,
                conversation_history=conversation_history,
                state=state,
            )
        elif intent == IntentType.REPORT:
            result = await self._handle_report(
                user_input=user_input,
                user_id=user_id,
                session_id=session_id,
                image_path=image_path,
                state=state,
            )
        else:  # GENERAL
            result = await self._handle_general(
                user_input=user_input,
                user_id=user_id,
                session_id=session_id,
                conversation_history=conversation_history,
            )

        return result

    async def _handle_triage(
        self,
        user_input: str,
        user_id: str,
        session_id: Optional[str],
        conversation_history: Optional[list],
        state: Optional[dict],
    ) -> dict:
        """
        处理导诊请求

        Args:
            user_input: 用户输入
            user_id: 用户ID
            session_id: 会话ID
            conversation_history: 对话历史
            state: 当前状态

        Returns:
            处理结果
        """
        logger.info("处理导诊请求")

        # 构建或更新状态
        if state and state.get("intent") == IntentType.TRIAGE:
            # 追问场景：更新现有状态
            triage_state = state.get("triage_state")
            if triage_state:
                triage_state["user_input"] = user_input
                triage_state["conversation_history"].append({
                    "role": "user",
                    "content": user_input,
                })
        else:
            # 新建状态
            triage_state = TriageState(
                user_input=user_input,
                conversation_history=conversation_history or [],
                symptoms=[],
                symptom_details={},
                info_completeness=0.0,
                recommended_departments=[],
                followup_questions=[],
                followup_rounds=0,
                advice="",
                response="",
            )

        # 执行导诊
        result_state = await self.triage_agent.process(user_input, triage_state)

        return {
            "intent": IntentType.TRIAGE,
            "safety_flag": "safe",
            "blocked": False,
            "response": result_state.get("response", ""),
            "state": {
                "intent": IntentType.TRIAGE,
                "triage_state": result_state,
            },
            "metadata": {
                "symptoms": result_state.get("symptoms", []),
                "departments": result_state.get("recommended_departments", []),
                "followup_rounds": result_state.get("followup_rounds", 0),
            },
        }

    async def _handle_report(
        self,
        user_input: str,
        user_id: str,
        session_id: Optional[str],
        image_path: Optional[str],
        state: Optional[dict],
    ) -> dict:
        """
        处理报告解读请求

        Args:
            user_input: 用户输入
            user_id: 用户ID
            session_id: 会话ID
            image_path: 图片路径
            state: 当前状态

        Returns:
            处理结果
        """
        logger.info("处理报告解读请求")

        # 如果没有图片，提示用户上传
        if not image_path:
            return {
                "intent": IntentType.REPORT,
                "safety_flag": "safe",
                "blocked": False,
                "response": "请上传您的医疗报告图片，我将为您解读。",
                "state": state,
                "metadata": {"require_image": True},
            }

        # 生成报告ID
        import uuid
        report_id = str(uuid.uuid4())

        # 执行报告解读
        result_state = await self.report_agent.process(
            report_id=report_id,
            user_id=user_id,
            image_path=image_path,
            session_id=session_id,
        )

        return {
            "intent": IntentType.REPORT,
            "safety_flag": "safe",
            "blocked": False,
            "response": result_state.get("response", ""),
            "state": {
                "intent": IntentType.REPORT,
                "report_state": result_state,
            },
            "metadata": {
                "report_id": report_id,
                "risk_level": result_state.get("risk_level", "normal"),
                "abnormal_count": len(result_state.get("abnormal_items", [])),
            },
        }

    async def _handle_general(
        self,
        user_input: str,
        user_id: str,
        session_id: Optional[str],
        conversation_history: Optional[list],
    ) -> dict:
        """
        处理通用问答请求

        Args:
            user_input: 用户输入
            user_id: 用户ID
            session_id: 会话ID
            conversation_history: 对话历史

        Returns:
            处理结果
        """
        logger.info("处理通用问答请求")

        # 执行通用问答
        response = await self.general_agent.process(
            user_input=user_input,
            conversation_history=conversation_history or [],
        )

        return {
            "intent": IntentType.GENERAL,
            "safety_flag": "safe",
            "blocked": False,
            "response": response,
            "state": {
                "intent": IntentType.GENERAL,
            },
            "metadata": {},
        }

    def get_agent_info(self) -> dict:
        """
        获取智能体信息

        Returns:
            智能体信息字典
        """
        return {
            "router": {
                "name": "MediRouter",
                "description": "意图路由智能体",
                "intents": ["triage", "report", "general"],
            },
            "triage": {
                "name": "TriageAgent",
                "description": "导诊智能体",
                "nodes": 7,
            },
            "report": {
                "name": "ReportAgent",
                "description": "报告解读智能体",
                "nodes": 9,
            },
            "general": {
                "name": "GeneralAgent",
                "description": "通用问答智能体",
                "nodes": 5,
            },
        }


# 全局Orchestrator实例
orchestrator = Orchestrator()
