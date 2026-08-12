"""
医疗导诊与报告解读助手 - TriageAgent导诊智能体

7节点流程：
1. parse_symptom - LLM提取症状实体
2. extract_entities - 补充持续时间、严重程度、伴随症状
3. query_department_kb - Milvus混合检索症状→科室映射
4. check_info_completeness - 条件边检查信息完整性
5. ask_followup - 追问患者（interrupt）
6. recommend_department - Top-3科室推荐
7. generate_advice - 生成就医建议
"""

import json
from typing import Any, Optional
from typing_extensions import TypedDict

from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

from backend.core.llm_factory import llm_factory
from backend.core.embedder import embedder
from backend.core.knowledge_base import kb_client
from backend.core.logger import setup_logger
from backend.core.retry import with_retry, LLM_RETRY_CONFIG, MEDICAL_FALLBACK_CONFIG

logger = setup_logger(__name__)


class TriageState(TypedDict):
    """导诊状态"""
    # 用户输入
    user_input: str
    conversation_history: list[dict]

    # 症状信息
    symptoms: list[str]
    symptom_details: dict[str, Any]  # 包含duration, severity, accompanying_symptoms
    info_completeness: float

    # 科室推荐
    recommended_departments: list[dict]

    # 输出
    followup_questions: list[str]
    followup_rounds: int
    advice: str
    response: str


class TriageAgent:
    """导诊智能体"""

    def __init__(self):
        logger.info("初始化TriageAgent")
        self.max_followup_rounds = 3
        self.min_info_completeness = 0.6
        self._build_graph()

    def _build_graph(self) -> None:
        """构建LangGraph工作流"""
        workflow = StateGraph(TriageState)

        # 添加节点
        workflow.add_node("parse_symptom", self.parse_symptom)
        workflow.add_node("extract_entities", self.extract_entities)
        workflow.add_node("query_department_kb", self.query_department_kb)
        workflow.add_node("check_info_completeness", self.check_info_completeness)
        workflow.add_node("ask_followup", self.ask_followup)
        workflow.add_node("recommend_department", self.recommend_department)
        workflow.add_node("generate_advice", self.generate_advice)

        # 设置入口
        workflow.set_entry_point("parse_symptom")

        # 添加边
        workflow.add_edge("parse_symptom", "extract_entities")
        workflow.add_edge("extract_entities", "query_department_kb")
        workflow.add_edge("query_department_kb", "check_info_completeness")

        # 条件边：根据信息完整性决定是追问还是推荐
        workflow.add_conditional_edges(
            "check_info_completeness",
            self._should_ask_followup,
            {
                "ask_followup": "ask_followup",
                "recommend": "recommend_department",
            },
        )

        workflow.add_edge("ask_followup", "extract_entities")  # 追问后重新提取实体
        workflow.add_edge("recommend_department", "generate_advice")
        workflow.add_edge("generate_advice", END)

        # 编译图
        self.graph = workflow.compile()

    async def process(self, user_input: str, state: Optional[TriageState] = None) -> TriageState:
        """
        处理导诊请求

        Args:
            user_input: 用户输入
            state: 当前状态（用于追问场景）

        Returns:
            更新后的状态
        """
        logger.info(f"处理导诊请求: {user_input[:50]}...")

        # 初始化状态
        if state is None:
            state = TriageState(
                user_input=user_input,
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

        # 添加用户输入到对话历史
        state["conversation_history"].append({
            "role": "user",
            "content": user_input,
        })

        # 执行工作流
        result = await self.graph.ainvoke(state)

        return result

    @with_retry(retry_config=LLM_RETRY_CONFIG, fallback_config=MEDICAL_FALLBACK_CONFIG)
    async def parse_symptom(self, state: TriageState) -> dict:
        """
        解析症状实体

        使用LLM从用户输入中提取症状实体
        """
        logger.info("解析症状实体")

        user_input = state["user_input"]
        conversation_history = state.get("conversation_history", [])

        # 构建提示词
        system_message = """你是一个医疗导诊助手，需要从用户描述中提取症状实体。

请从用户输入中提取所有提到的症状，包括：
- 主要症状（如：头痛、发烧、咳嗽）
- 症状部位（如：头部、胸部、腹部）
- 症状特征（如：持续性、阵发性、刺痛）

输出格式为JSON数组，例如：["头痛", "发烧", "咳嗽"]
如果用户没有提到具体症状，返回空数组 []

注意：
1. 只提取明确提到的症状，不要推断
2. 使用常见的医学术语
3. 保持症状描述简洁"""

        # 构建对话历史
        messages = [{"role": "system", "content": system_message}]
        for msg in conversation_history[-5:]:  # 只保留最近5条消息
            messages.append(msg)

        # 调用LLM
        response = await llm_factory.invoke_with_messages(
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )

        # 解析响应
        try:
            # 尝试提取JSON
            if "[" in response and "]" in response:
                start = response.index("[")
                end = response.index("]") + 1
                symptoms = json.loads(response[start:end])
            else:
                symptoms = []
        except json.JSONDecodeError:
            symptoms = []

        logger.info(f"提取到症状: {symptoms}")

        return {"symptoms": symptoms}

    @with_retry(retry_config=LLM_RETRY_CONFIG, fallback_config=MEDICAL_FALLBACK_CONFIG)
    async def extract_entities(self, state: TriageState) -> dict:
        """
        提取症状实体详情

        补充持续时间、严重程度、伴随症状等信息
        """
        logger.info("提取症状实体详情")

        symptoms = state.get("symptoms", [])
        user_input = state["user_input"]
        conversation_history = state.get("conversation_history", [])

        if not symptoms:
            return {"symptom_details": {}}

        # 构建提示词
        system_message = """你是一个医疗导诊助手，需要从对话中提取症状的详细信息。

请分析用户描述，提取以下信息：
1. 持续时间（duration）：症状持续了多久
2. 严重程度（severity）：轻微/中等/严重
3. 伴随症状（accompanying_symptoms）：除了主要症状外，还有哪些伴随症状

输出格式为JSON对象，例如：
{
    "duration": "3天",
    "severity": "中等",
    "accompanying_symptoms": ["乏力", "食欲不振"]
}

如果信息不明确，对应字段返回null。"""

        # 构建对话历史
        messages = [{"role": "system", "content": system_message}]
        for msg in conversation_history[-5:]:
            messages.append(msg)
        messages.append({"role": "user", "content": f"主要症状：{', '.join(symptoms)}\n\n请从对话中提取这些症状的详细信息。"})

        # 调用LLM
        response = await llm_factory.invoke_with_messages(
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )

        # 解析响应
        try:
            if "{" in response and "}" in response:
                start = response.index("{")
                end = response.index("}") + 1
                details = json.loads(response[start:end])
            else:
                details = {}
        except json.JSONDecodeError:
            details = {}

        logger.info(f"症状详情: {details}")

        return {"symptom_details": details}

    async def query_department_kb(self, state: TriageState) -> dict:
        """
        查询科室知识库

        使用Milvus混合检索症状→科室映射
        """
        logger.info("查询科室知识库")

        symptoms = state.get("symptoms", [])
        symptom_details = state.get("symptom_details", {})

        if not symptoms:
            return {"recommended_departments": []}

        # 构建查询文本
        query_parts = symptoms.copy()
        if symptom_details.get("accompanying_symptoms"):
            query_parts.extend(symptom_details["accompanying_symptoms"])
        query_text = " ".join(query_parts)

        try:
            # 使用Embedding生成向量
            from backend.core.embedder import embedder
            query_embedding = embedder.encode_single(query_text)

            # 使用Milvus检索
            from backend.core.knowledge_base import kb_client
            results = kb_client.search_symptoms(
                query_embedding=query_embedding.tolist(),
                top_k=5,
            )

            # 格式化结果
            departments = []
            for result in results:
                departments.append({
                    "department": result.get("department", ""),
                    "confidence": result.get("score", 0),
                    "description": result.get("description", ""),
                })

            logger.info(f"检索到科室: {[d['department'] for d in departments]}")

            return {"recommended_departments": departments}

        except Exception as e:
            logger.error(f"科室检索失败: {e}")
            # 返回默认科室
            return {
                "recommended_departments": [
                    {"department": "全科", "confidence": 0.5, "description": "建议先到全科就诊"},
                ]
            }

    def check_info_completeness(self, state: TriageState) -> dict:
        """
        检查信息完整性

        评估症状信息是否足够进行科室推荐
        """
        logger.info("检查信息完整性")

        symptoms = state.get("symptoms", [])
        symptom_details = state.get("symptom_details", {})
        recommended_departments = state.get("recommended_departments", [])

        # 计算完整性分数
        score = 0.0

        # 有症状 +0.4
        if symptoms:
            score += 0.4

        # 有持续时间 +0.2
        if symptom_details.get("duration"):
            score += 0.2

        # 有严重程度 +0.2
        if symptom_details.get("severity"):
            score += 0.2

        # 有伴随症状 +0.1
        if symptom_details.get("accompanying_symptoms"):
            score += 0.1

        # 有科室推荐结果 +0.1
        if recommended_departments:
            score += 0.1

        logger.info(f"信息完整性分数: {score}")

        return {"info_completeness": score}

    def _should_ask_followup(self, state: TriageState) -> str:
        """
        条件边：判断是否需要追问

        Returns:
            "ask_followup" 或 "recommend"
        """
        info_completeness = state.get("info_completeness", 0)
        followup_rounds = state.get("followup_rounds", 0)

        # 如果信息完整性不足且追问轮数未达上限，则追问
        if info_completeness < self.min_info_completeness and followup_rounds < self.max_followup_rounds:
            return "ask_followup"
        return "recommend"

    @with_retry(retry_config=LLM_RETRY_CONFIG, fallback_config=MEDICAL_FALLBACK_CONFIG)
    async def ask_followup(self, state: TriageState) -> dict:
        """
        生成追问问题

        使用interrupt机制暂停，等待患者回答
        """
        logger.info("生成追问问题")

        symptoms = state.get("symptoms", [])
        symptom_details = state.get("symptom_details", {})
        conversation_history = state.get("conversation_history", [])
        followup_rounds = state.get("followup_rounds", 0)

        # 构建提示词
        system_message = """你是一个医疗导诊助手，需要向患者询问更多信息以更好地推荐科室。

请根据已知的症状信息，生成1-2个简短的追问问题，帮助了解：
1. 症状的持续时间（如果不知道）
2. 症状的严重程度（如果不知道）
3. 是否有其他伴随症状（如果不知道）
4. 症状的具体特征（如疼痛性质、部位等）

输出格式为JSON数组，例如：["症状持续多久了？", "疼痛是刺痛还是钝痛？"]

注意：
1. 问题要简洁明了
2. 不要重复已知信息
3. 最多问2个问题"""

        # 构建已知信息
        known_info = f"已知症状：{', '.join(symptoms) if symptoms else '无'}\n"
        if symptom_details.get("duration"):
            known_info += f"持续时间：{symptom_details['duration']}\n"
        if symptom_details.get("severity"):
            known_info += f"严重程度：{symptom_details['severity']}\n"
        if symptom_details.get("accompanying_symptoms"):
            known_info += f"伴随症状：{', '.join(symptom_details['accompanying_symptoms'])}\n"

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": known_info},
        ]

        # 调用LLM
        response = await llm_factory.invoke_with_messages(
            messages=messages,
            temperature=0.5,
            max_tokens=300,
        )

        # 解析响应
        try:
            if "[" in response and "]" in response:
                start = response.index("[")
                end = response.index("]") + 1
                followup_questions = json.loads(response[start:end])
            else:
                followup_questions = ["请详细描述一下您的症状。"]
        except json.JSONDecodeError:
            followup_questions = ["请详细描述一下您的症状。"]

        logger.info(f"追问问题: {followup_questions}")

        # 使用interrupt机制暂停，等待患者回答
        # interrupt会抛出异常，中断当前执行
        user_response = interrupt({
            "type": "followup",
            "questions": followup_questions,
            "round": followup_rounds + 1,
        })

        # 用户回答后，更新对话历史
        conversation_history.append({
            "role": "assistant",
            "content": " ".join(followup_questions),
        })
        conversation_history.append({
            "role": "user",
            "content": user_response,
        })

        return {
            "followup_questions": followup_questions,
            "followup_rounds": followup_rounds + 1,
            "conversation_history": conversation_history,
            "user_input": user_response,
        }

    @with_retry(retry_config=LLM_RETRY_CONFIG, fallback_config=MEDICAL_FALLBACK_CONFIG)
    async def recommend_department(self, state: TriageState) -> dict:
        """
        推荐科室

        生成Top-3科室推荐及置信度
        """
        logger.info("推荐科室")

        symptoms = state.get("symptoms", [])
        symptom_details = state.get("symptom_details", {})
        recommended_departments = state.get("recommended_departments", [])

        # 如果没有检索到科室，使用LLM推荐
        if not recommended_departments:
            system_message = """你是一个医疗导诊助手，需要根据症状推荐就诊科室。

请根据用户描述的症状，推荐最合适的3个科室，按优先级排序。

输出格式为JSON数组，例如：
[
    {"department": "神经内科", "reason": "头痛可能与神经系统相关"},
    {"department": "眼科", "reason": "如果伴有视力问题"},
    {"department": "耳鼻喉科", "reason": "如果伴有头晕"}
]

注意：
1. 推荐要基于症状的医学关联性
2. 优先推荐最可能的科室
3. 给出推荐理由"""

            # 构建症状描述
            symptom_desc = f"症状：{', '.join(symptoms)}\n"
            if symptom_details.get("duration"):
                symptom_desc += f"持续时间：{symptom_details['duration']}\n"
            if symptom_details.get("severity"):
                symptom_desc += f"严重程度：{symptom_details['severity']}\n"
            if symptom_details.get("accompanying_symptoms"):
                symptom_desc += f"伴随症状：{', '.join(symptom_details['accompanying_symptoms'])}\n"

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": symptom_desc},
            ]

            # 调用LLM
            response = await llm_factory.invoke_with_messages(
                messages=messages,
                temperature=0.3,
                max_tokens=500,
            )

            # 解析响应
            try:
                if "[" in response and "]" in response:
                    start = response.index("[")
                    end = response.index("]") + 1
                    recommended_departments = json.loads(response[start:end])
                else:
                    recommended_departments = [
                        {"department": "全科", "reason": "建议先到全科就诊进行初步评估"}
                    ]
            except json.JSONDecodeError:
                recommended_departments = [
                    {"department": "全科", "reason": "建议先到全科就诊进行初步评估"}
                ]

        # 确保只返回Top-3
        recommended_departments = recommended_departments[:3]

        logger.info(f"推荐科室: {[d['department'] for d in recommended_departments]}")

        return {"recommended_departments": recommended_departments}

    @with_retry(retry_config=LLM_RETRY_CONFIG, fallback_config=MEDICAL_FALLBACK_CONFIG)
    async def generate_advice(self, state: TriageState) -> dict:
        """
        生成就医建议

        生成就医建议、检查建议和注意事项
        """
        logger.info("生成就医建议")

        symptoms = state.get("symptoms", [])
        symptom_details = state.get("symptom_details", {})
        recommended_departments = state.get("recommended_departments", [])

        # 构建提示词
        system_message = """你是一个医疗导诊助手，需要为患者提供就医建议。

请根据症状和推荐科室，生成以下内容：
1. 就医建议：应该去哪个科室，优先级如何
2. 检查建议：可能需要做哪些检查
3. 注意事项：就医前需要注意什么

输出格式为JSON对象：
{
    "visit_advice": "建议首先到神经内科就诊...",
    "examination_advice": "可能需要做头部CT、血常规等检查...",
    "precautions": "就医前注意记录症状发作时间..."
}

注意：
1. 建议要具体实用
2. 不要给出诊断结论
3. 提醒患者遵医嘱"""

        # 构建上下文
        context = f"症状：{', '.join(symptoms)}\n"
        if symptom_details.get("duration"):
            context += f"持续时间：{symptom_details['duration']}\n"
        if symptom_details.get("severity"):
            context += f"严重程度：{symptom_details['severity']}\n"
        if recommended_departments:
            context += f"推荐科室：{', '.join([d['department'] for d in recommended_departments])}\n"

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": context},
        ]

        # 调用LLM
        response = await llm_factory.invoke_with_messages(
            messages=messages,
            temperature=0.5,
            max_tokens=800,
        )

        # 解析响应
        try:
            if "{" in response and "}" in response:
                start = response.index("{")
                end = response.index("}") + 1
                advice_data = json.loads(response[start:end])
            else:
                advice_data = {
                    "visit_advice": "建议到医院就诊",
                    "examination_advice": "由医生根据情况决定检查项目",
                    "precautions": "就医前注意记录症状",
                }
        except json.JSONDecodeError:
            advice_data = {
                "visit_advice": "建议到医院就诊",
                "examination_advice": "由医生根据情况决定检查项目",
                "precautions": "就医前注意记录症状",
            }

        # 构建最终回复
        response_text = self._build_response(
            symptoms=symptoms,
            departments=recommended_departments,
            advice=advice_data,
        )

        logger.info("就医建议生成完成")

        return {
            "advice": advice_data,
            "response": response_text,
        }

    def _build_response(
        self,
        symptoms: list[str],
        departments: list[dict],
        advice: dict,
    ) -> str:
        """构建最终回复"""
        lines = []
        lines.append("## 导诊结果\n")

        # 症状总结
        if symptoms:
            lines.append(f"**您的症状**：{', '.join(symptoms)}\n")

        # 科室推荐
        if departments:
            lines.append("**推荐科室**：\n")
            for i, dept in enumerate(departments, 1):
                lines.append(f"{i}. **{dept['department']}**")
                if dept.get("reason"):
                    lines.append(f"   - {dept['reason']}")
            lines.append("")

        # 就医建议
        if advice.get("visit_advice"):
            lines.append(f"**就医建议**：{advice['visit_advice']}\n")

        if advice.get("examination_advice"):
            lines.append(f"**可能检查**：{advice['examination_advice']}\n")

        if advice.get("precautions"):
            lines.append(f"**注意事项**：{advice['precautions']}\n")

        # 免责声明
        lines.append("---")
        lines.append("*以上建议仅供参考，具体诊疗请遵医嘱。如有紧急情况，请拨打120急救电话。*")

        return "\n".join(lines)


# 全局TriageAgent实例
triage_agent = TriageAgent()
