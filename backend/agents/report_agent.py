"""
医疗导诊与报告解读助手 - ReportAgent报告解读智能体

9节点流程：
1. parse_report_image - 多模态模型OCR识别化验单
2. extract_lab_values - 结构化提取检验数据
3. lab_value_query - MySQL结构化查询参考值
4. identify_abnormalities - 对比标记异常指标
5. analyze_risk_level - 三级风险评估
6. query_medical_guidelines - Milvus RAG检索医学指南
7. generate_interpretation - 生成解读草案
8. HITL interrupt - 医生审核
9. apply_doctor_decision - 应用医生决策
"""

import json
from datetime import datetime
from typing import Any, Optional
from typing_extensions import TypedDict

from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

from backend.core.llm_factory import llm_factory
from backend.core.logger import setup_logger
from backend.core.retry import with_retry, LLM_RETRY_CONFIG, MEDICAL_FALLBACK_CONFIG

logger = setup_logger(__name__)


class ReportState(TypedDict):
    """报告解读状态"""
    # 输入
    report_id: str
    user_id: str
    image_path: str
    session_id: Optional[str]

    # OCR结果
    ocr_raw_data: str
    parsed_lab_values: list[dict]

    # 检验指标查询结果
    lab_values_with_reference: list[dict]

    # 异常识别
    abnormal_items: list[dict]

    # 风险评估
    risk_level: str  # "normal" | "attention" | "see_doctor"

    # 医学指南
    relevant_guidelines: list[str]

    # 解读
    interpretation: str

    # HITL审核
    pending_review: bool
    review_status: str  # "pending" | "approved" | "modified" | "rejected"
    doctor_comment: str
    doctor_modified_text: str
    degraded_output: bool

    # 输出
    response: str
    audit_log: list[dict]


class ReportAgent:
    """报告解读智能体"""

    def __init__(self):
        logger.info("初始化ReportAgent")
        self.hitl_timeout_minutes = 60
        self._build_graph()

    def _build_graph(self) -> None:
        """构建LangGraph工作流"""
        workflow = StateGraph(ReportState)

        # 添加节点
        workflow.add_node("parse_report_image", self.parse_report_image)
        workflow.add_node("extract_lab_values", self.extract_lab_values)
        workflow.add_node("lab_value_query", self.lab_value_query)
        workflow.add_node("identify_abnormalities", self.identify_abnormalities)
        workflow.add_node("analyze_risk_level", self.analyze_risk_level)
        workflow.add_node("query_medical_guidelines", self.query_medical_guidelines)
        workflow.add_node("generate_interpretation", self.generate_interpretation)
        workflow.add_node("hitl_review", self.hitl_review)
        workflow.add_node("apply_doctor_decision", self.apply_doctor_decision)

        # 设置入口
        workflow.set_entry_point("parse_report_image")

        # 添加边
        workflow.add_edge("parse_report_image", "extract_lab_values")
        workflow.add_edge("extract_lab_values", "lab_value_query")
        workflow.add_edge("lab_value_query", "identify_abnormalities")
        workflow.add_edge("identify_abnormalities", "analyze_risk_level")

        # 条件边：根据风险等级决定是否检索医学指南
        workflow.add_conditional_edges(
            "analyze_risk_level",
            self._should_query_guidelines,
            {
                "query_guidelines": "query_medical_guidelines",
                "skip_guidelines": "generate_interpretation",
            },
        )

        workflow.add_edge("query_medical_guidelines", "generate_interpretation")
        workflow.add_edge("generate_interpretation", "hitl_review")
        workflow.add_edge("hitl_review", "apply_doctor_decision")
        workflow.add_edge("apply_doctor_decision", END)

        # 编译图
        self.graph = workflow.compile()

    async def process(
        self,
        report_id: str,
        user_id: str,
        image_path: str,
        session_id: Optional[str] = None,
    ) -> ReportState:
        """
        处理报告解读请求

        Args:
            report_id: 报告ID
            user_id: 用户ID
            image_path: 图片路径
            session_id: 会话ID

        Returns:
            解读结果状态
        """
        logger.info(f"处理报告解读请求: {report_id}")

        # 初始化状态
        state = ReportState(
            report_id=report_id,
            user_id=user_id,
            image_path=image_path,
            session_id=session_id,
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

        # 执行工作流
        result = await self.graph.ainvoke(state)

        return result

    @with_retry(retry_config=LLM_RETRY_CONFIG, fallback_config=MEDICAL_FALLBACK_CONFIG)
    async def parse_report_image(self, state: ReportState) -> dict:
        """
        OCR识别报告图片

        使用多模态模型识别化验单
        """
        logger.info("OCR识别报告图片")

        image_path = state["image_path"]

        # 构建提示词
        system_message = """你是一个医疗报告OCR识别助手，需要从化验单图片中提取文字信息。

请识别图片中的所有文字内容，包括：
1. 患者信息（姓名、性别、年龄、送检日期等）
2. 检验项目（项目名称、结果值、参考范围、单位）
3. 医院信息（医院名称、科室等）
4. 其他备注信息

输出格式为JSON对象：
{
    "patient_info": {
        "name": "患者姓名",
        "gender": "性别",
        "age": "年龄",
        "date": "送检日期"
    },
    "lab_items": [
        {
            "item_name": "项目名称",
            "result": "结果值",
            "reference_range": "参考范围",
            "unit": "单位"
        }
    ],
    "hospital_info": {
        "name": "医院名称",
        "department": "科室"
    },
    "other_info": "其他备注"
}

注意：
1. 准确识别数字和单位
2. 如果看不清，用null表示
3. 保持原始数据的准确性"""

        # 调用LLM（这里假设使用多模态模型）
        # 在实际实现中，需要使用支持图片的模型
        response = await llm_factory.invoke(
            prompt=f"请识别以下化验单图片中的内容：{image_path}",
            system_message=system_message,
            temperature=0.3,
            max_tokens=2000,
        )

        # 解析响应
        try:
            if "{" in response and "}" in response:
                start = response.index("{")
                end = response.index("}") + 1
                ocr_data = json.loads(response[start:end])
            else:
                ocr_data = {"raw_text": response}
        except json.JSONDecodeError:
            ocr_data = {"raw_text": response}

        logger.info("OCR识别完成")

        return {
            "ocr_raw_data": response,
            "parsed_lab_values": ocr_data.get("lab_items", []),
        }

    @with_retry(retry_config=LLM_RETRY_CONFIG, fallback_config=MEDICAL_FALLBACK_CONFIG)
    async def extract_lab_values(self, state: ReportState) -> dict:
        """
        结构化提取检验数据

        从OCR结果中提取标准化的检验数据
        """
        logger.info("结构化提取检验数据")

        parsed_lab_values = state.get("parsed_lab_values", [])

        if not parsed_lab_values:
            return {"parsed_lab_values": []}

        # 构建提示词
        system_message = """你是一个医疗数据处理助手，需要将检验数据标准化。

请将以下检验数据标准化，确保：
1. 项目名称使用标准医学术语
2. 结果值转为数字类型
3. 单位统一
4. 参考范围解析为数值

输出格式为JSON数组：
[
    {
        "item_name": "标准项目名称",
        "item_name_en": "英文名称",
        "value": 123.45,
        "unit": "单位",
        "reference_low": 下限值,
        "reference_high": 上限值,
        "original_data": 原始数据
    }
]

注意：
1. 如果结果值无法转为数字，保持原样
2. 参考范围可能是区间（如3.5-5.5）或上限（如<100）
3. 保留原始数据以便核对"""

        # 调用LLM
        response = await llm_factory.invoke(
            prompt=f"请标准化以下检验数据：\n{json.dumps(parsed_lab_values, ensure_ascii=False)}",
            system_message=system_message,
            temperature=0.3,
            max_tokens=2000,
        )

        # 解析响应
        try:
            if "[" in response and "]" in response:
                start = response.index("[")
                end = response.index("]") + 1
                standardized_values = json.loads(response[start:end])
            else:
                standardized_values = parsed_lab_values
        except json.JSONDecodeError:
            standardized_values = parsed_lab_values

        logger.info(f"提取到 {len(standardized_values)} 个检验指标")

        return {"parsed_lab_values": standardized_values}

    async def lab_value_query(self, state: ReportState) -> dict:
        """
        查询检验指标参考值

        使用MySQL结构化查询
        """
        logger.info("查询检验指标参考值")

        parsed_lab_values = state.get("parsed_lab_values", [])

        if not parsed_lab_values:
            return {"lab_values_with_reference": []}

        # 使用LabValueDB查询
        try:
            from backend.core.lab_value_db import get_lab_value_db
            from backend.dependencies import SessionLocal

            db = SessionLocal()
            lab_db = get_lab_value_db(db)

            # 提取项目名称
            item_names = [v.get("item_name", "") for v in parsed_lab_values]

            # 批量查询
            references = lab_db.batch_query(item_names)

            # 合并结果
            lab_values_with_reference = []
            for lab_value in parsed_lab_values:
                item_name = lab_value.get("item_name", "")
                ref = next((r for r in references if r.item_name == item_name), None)

                result = lab_value.copy()
                if ref:
                    result["reference_low"] = ref.reference_range_low
                    result["reference_high"] = ref.reference_range_high
                    result["clinical_significance"] = ref.clinical_significance
                    result["abnormal_high_meaning"] = ref.abnormal_high_meaning
                    result["abnormal_low_meaning"] = ref.abnormal_low_meaning

                lab_values_with_reference.append(result)

            db.close()

        except Exception as e:
            logger.error(f"查询检验指标参考值失败: {e}")
            lab_values_with_reference = parsed_lab_values

        logger.info(f"查询到 {len(lab_values_with_reference)} 个指标的参考值")

        return {"lab_values_with_reference": lab_values_with_reference}

    async def identify_abnormalities(self, state: ReportState) -> dict:
        """
        识别异常指标

        对比参考范围，标记异常
        """
        logger.info("识别异常指标")

        lab_values_with_reference = state.get("lab_values_with_reference", [])

        if not lab_values_with_reference:
            return {"abnormal_items": []}

        abnormal_items = []

        for item in lab_values_with_reference:
            value = item.get("value")
            ref_low = item.get("reference_low")
            ref_high = item.get("reference_high")

            if value is None or (ref_low is None and ref_high is None):
                continue

            try:
                value = float(value)
            except (ValueError, TypeError):
                continue

            is_abnormal = False
            abnormal_type = None
            meaning = None

            # 检查是否偏低
            if ref_low is not None and value < ref_low:
                is_abnormal = True
                abnormal_type = "low"
                meaning = item.get("abnormal_low_meaning", "")

            # 检查是否偏高
            if ref_high is not None and value > ref_high:
                is_abnormal = True
                abnormal_type = "high"
                meaning = item.get("abnormal_high_meaning", "")

            if is_abnormal:
                abnormal_items.append({
                    "item_name": item.get("item_name", ""),
                    "value": value,
                    "unit": item.get("unit", ""),
                    "reference_range": f"{ref_low or ''}-{ref_high or ''}",
                    "abnormal_type": abnormal_type,
                    "meaning": meaning,
                })

        logger.info(f"识别到 {len(abnormal_items)} 个异常指标")

        return {"abnormal_items": abnormal_items}

    async def analyze_risk_level(self, state: ReportState) -> dict:
        """
        分析风险等级

        根据异常指标评估风险
        """
        logger.info("分析风险等级")

        abnormal_items = state.get("abnormal_items", [])

        if not abnormal_items:
            return {"risk_level": "normal"}

        # 构建提示词
        system_message = """你是一个医疗风险评估助手，需要根据异常检验指标评估风险等级。

请根据以下异常指标，评估风险等级：
- normal: 所有指标正常或轻微异常，无需特别关注
- attention: 有指标异常，建议关注，可能需要复查
- see_doctor: 有明显异常指标，建议尽快就医

输出格式为JSON对象：
{
    "risk_level": "normal/attention/see_doctor",
    "reason": "评估理由"
}

注意：
1. 综合考虑所有异常指标
2. 关注指标的临床意义
3. 给出合理的评估理由"""

        # 调用LLM
        response = await llm_factory.invoke(
            prompt=f"请评估以下异常指标的风险等级：\n{json.dumps(abnormal_items, ensure_ascii=False)}",
            system_message=system_message,
            temperature=0.3,
            max_tokens=500,
        )

        # 解析响应
        try:
            if "{" in response and "}" in response:
                start = response.index("{")
                end = response.index("}") + 1
                risk_data = json.loads(response[start:end])
                risk_level = risk_data.get("risk_level", "attention")
            else:
                risk_level = "attention"
        except json.JSONDecodeError:
            risk_level = "attention"

        logger.info(f"风险等级: {risk_level}")

        return {"risk_level": risk_level}

    def _should_query_guidelines(self, state: ReportState) -> str:
        """
        条件边：判断是否需要检索医学指南

        Returns:
            "query_guidelines" 或 "skip_guidelines"
        """
        risk_level = state.get("risk_level", "normal")

        # 高风险时检索医学指南
        if risk_level in ["attention", "see_doctor"]:
            return "query_guidelines"
        return "skip_guidelines"

    async def query_medical_guidelines(self, state: ReportState) -> dict:
        """
        查询医学指南

        使用Milvus RAG检索
        """
        logger.info("查询医学指南")

        abnormal_items = state.get("abnormal_items", [])

        if not abnormal_items:
            return {"relevant_guidelines": []}

        try:
            # 构建查询文本
            query_parts = [item.get("item_name", "") for item in abnormal_items]
            query_text = " ".join(query_parts)

            # 使用Embedding生成向量
            from backend.core.embedder import embedder
            query_embedding = embedder.encode_single(query_text)

            # 使用Milvus检索
            from backend.core.knowledge_base import kb_client
            results = kb_client.search_guidelines(
                query_embedding=query_embedding.tolist(),
                top_k=3,
            )

            # 提取指南内容
            guidelines = [result.get("content", "") for result in results]

            logger.info(f"检索到 {len(guidelines)} 条医学指南")

            return {"relevant_guidelines": guidelines}

        except Exception as e:
            logger.error(f"查询医学指南失败: {e}")
            return {"relevant_guidelines": []}

    @with_retry(retry_config=LLM_RETRY_CONFIG, fallback_config=MEDICAL_FALLBACK_CONFIG)
    async def generate_interpretation(self, state: ReportState) -> dict:
        """
        生成解读草案

        生成通俗易懂的解读文本
        """
        logger.info("生成解读草案")

        abnormal_items = state.get("abnormal_items", [])
        risk_level = state.get("risk_level", "normal")
        guidelines = state.get("relevant_guidelines", [])

        # 构建提示词
        system_message = """你是一个医疗报告解读助手，需要为患者生成通俗易懂的报告解读。

请根据以下信息生成解读：
1. 异常指标列表及其含义
2. 风险等级评估
3. 相关医学指南（如有）

输出格式为JSON对象：
{
    "summary": "总体评估摘要",
    "details": [
        {
            "item_name": "指标名称",
            "explanation": "通俗解释",
            "suggestion": "建议"
        }
    ],
    "recommendations": ["建议1", "建议2"],
    "disclaimer": "免责声明"
}

注意：
1. 使用通俗易懂的语言
2. 避免专业术语
3. 给出实用建议
4. 包含免责声明"""

        # 构建上下文
        context = f"异常指标：\n{json.dumps(abnormal_items, ensure_ascii=False)}\n\n"
        context += f"风险等级：{risk_level}\n\n"
        if guidelines:
            context += f"相关指南：\n{chr(10).join(guidelines[:3])}\n"

        # 调用LLM
        response = await llm_factory.invoke(
            prompt=f"请生成报告解读：\n{context}",
            system_message=system_message,
            temperature=0.5,
            max_tokens=2000,
        )

        # 解析响应
        try:
            if "{" in response and "}" in response:
                start = response.index("{")
                end = response.index("}") + 1
                interpretation_data = json.loads(response[start:end])
                interpretation = self._format_interpretation(interpretation_data)
            else:
                interpretation = response
        except json.JSONDecodeError:
            interpretation = response

        logger.info("解读草案生成完成")

        return {"interpretation": interpretation}

    def _format_interpretation(self, data: dict) -> str:
        """格式化解读文本"""
        lines = []

        # 总体评估
        if data.get("summary"):
            lines.append(f"## 总体评估\n{data['summary']}\n")

        # 详细解读
        if data.get("details"):
            lines.append("## 详细解读\n")
            for detail in data["details"]:
                lines.append(f"**{detail.get('item_name', '')}**")
                lines.append(f"- {detail.get('explanation', '')}")
                if detail.get("suggestion"):
                    lines.append(f"- 建议：{detail['suggestion']}")
                lines.append("")

        # 建议
        if data.get("recommendations"):
            lines.append("## 建议\n")
            for i, rec in enumerate(data["recommendations"], 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        # 免责声明
        if data.get("disclaimer"):
            lines.append(f"---\n*{data['disclaimer']}*")

        return "\n".join(lines)

    async def hitl_review(self, state: ReportState) -> dict:
        """
        医生HITL审核

        使用interrupt机制暂停，等待医生审核
        """
        logger.info("提交医生审核")

        interpretation = state.get("interpretation", "")
        abnormal_items = state.get("abnormal_items", [])
        ocr_raw_data = state.get("ocr_raw_data", "")

        # 使用interrupt机制暂停，等待医生审核
        review_result = interrupt({
            "type": "report_review",
            "report_id": state["report_id"],
            "ocr_data": ocr_raw_data,
            "abnormal_items": abnormal_items,
            "interpretation": interpretation,
            "risk_level": state.get("risk_level", "normal"),
        })

        # 解析审核结果
        return {
            "review_status": review_result.get("status", "pending"),
            "doctor_comment": review_result.get("comment", ""),
            "doctor_modified_text": review_result.get("modified_text", ""),
            "pending_review": False,
        }

    async def apply_doctor_decision(self, state: ReportState) -> dict:
        """
        应用医生决策

        根据审核结果生成最终输出
        """
        logger.info("应用医生决策")

        review_status = state.get("review_status", "pending")
        interpretation = state.get("interpretation", "")
        doctor_modified_text = state.get("doctor_modified_text", "")
        doctor_comment = state.get("doctor_comment", "")
        degraded_output = state.get("degraded_output", False)

        # 根据审核状态生成最终输出
        if review_status == "approved":
            # 批准：使用AI解读
            final_text = interpretation
        elif review_status == "modified":
            # 修改：使用医生修改后的文本
            final_text = doctor_modified_text
        elif review_status == "rejected":
            # 驳回：建议线下就诊
            final_text = "建议您前往医院进行专业咨询和诊断。"
        else:
            # 超时或其他：降级输出
            final_text = interpretation
            if degraded_output:
                final_text += "\n\n*注意：本解读未经医生审核，仅供参考。*"

        # 构建最终回复
        response = self._build_final_response(
            final_text=final_text,
            abnormal_items=state.get("abnormal_items", []),
            risk_level=state.get("risk_level", "normal"),
            doctor_comment=doctor_comment,
            review_status=review_status,
        )

        # 记录审计日志
        audit_log = state.get("audit_log", [])
        audit_log.append({
            "node": "apply_doctor_decision",
            "action": "generate_final_response",
            "timestamp": str(datetime.now()),
            "review_status": review_status,
        })

        logger.info(f"最终输出生成完成，审核状态: {review_status}")

        return {
            "response": response,
            "audit_log": audit_log,
        }

    def _build_final_response(
        self,
        final_text: str,
        abnormal_items: list[dict],
        risk_level: str,
        doctor_comment: str,
        review_status: str,
    ) -> str:
        """构建最终回复"""
        lines = []

        # 风险等级标签
        risk_labels = {
            "normal": "🟢 正常",
            "attention": "🟡 关注",
            "see_doctor": "🔴 就医",
        }
        risk_label = risk_labels.get(risk_level, "未知")

        lines.append(f"## 报告解读结果\n")
        lines.append(f"**风险等级**：{risk_label}\n")

        # 异常指标
        if abnormal_items:
            lines.append("**异常指标**：\n")
            for item in abnormal_items:
                abnormal_type = "↑偏高" if item.get("abnormal_type") == "high" else "↓偏低"
                lines.append(
                    f"- {item.get('item_name', '')}: "
                    f"{item.get('value', '')} {item.get('unit', '')} "
                    f"({abnormal_type}, 参考范围: {item.get('reference_range', '')})"
                )
            lines.append("")

        # 解读内容
        lines.append("**解读内容**：\n")
        lines.append(final_text)
        lines.append("")

        # 医生批注
        if doctor_comment and review_status in ["approved", "modified"]:
            lines.append(f"**医生批注**：{doctor_comment}\n")

        # 审核状态说明
        if review_status == "approved":
            lines.append("*本解读已经过医生审核。*")
        elif review_status == "modified":
            lines.append("*本解读已经过医生修改。*")
        elif review_status == "rejected":
            lines.append("*医生建议您前往医院进行专业咨询。*")

        return "\n".join(lines)


# 全局ReportAgent实例
report_agent = ReportAgent()
