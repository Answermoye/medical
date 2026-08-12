"""
医疗导诊与报告解读助手 - 数据库模型
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

# 数据库模型基类
Base = declarative_base()


def generate_uuid() -> str:
    """生成UUID"""
    return str(uuid.uuid4())


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    phone = Column(String(20), unique=True, nullable=True)
    role = Column(
        Enum("patient", "doctor", "admin", name="user_role"),
        default="patient",
        nullable=False,
    )
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    sessions = relationship("Session", back_populates="user")
    reports = relationship("Report", back_populates="user")
    review_tasks = relationship("ReviewTask", back_populates="doctor", foreign_keys="ReviewTask.doctor_id")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class Session(Base):
    """会话表"""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    mode = Column(
        Enum("triage", "report", "general", name="session_mode"),
        nullable=False,
    )
    title = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", order_by="Message.created_at")

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, mode={self.mode})>"


class Message(Base):
    """消息表"""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    role = Column(
        Enum("user", "assistant", "system", name="message_role"),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    message_type = Column(
        Enum("text", "image", "file", name="message_type"),
        default="text",
    )
    extra_data = Column("metadata", JSON, nullable=True)  # 存储额外信息，如图片URL、文件路径等
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    session = relationship("Session", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role})>"


class Report(Base):
    """报告表"""
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=True)
    title = Column(String(200), nullable=True)
    image_path = Column(String(500), nullable=True)  # 原始报告图片路径
    ocr_raw_data = Column(Text, nullable=True)  # OCR原始识别结果
    parsed_data = Column(JSON, nullable=True)  # 结构化解析数据
    abnormal_items = Column(JSON, nullable=True)  # 异常指标列表
    risk_level = Column(
        Enum("normal", "attention", "see_doctor", name="risk_level"),
        nullable=True,
    )
    interpretation = Column(Text, nullable=True)  # AI解读文本
    status = Column(
        Enum("pending", "processing", "completed", "failed", name="report_status"),
        default="pending",
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="reports")
    review_task = relationship("ReviewTask", back_populates="report", uselist=False)

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, status={self.status})>"


class ReviewTask(Base):
    """医生审核任务表"""
    __tablename__ = "review_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=False, unique=True)
    doctor_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(
        Enum("pending", "approved", "modified", "rejected", name="review_status"),
        default="pending",
    )
    ai_interpretation = Column(Text, nullable=True)  # AI生成的解读
    doctor_comment = Column(Text, nullable=True)  # 医生批注
    doctor_modified_text = Column(Text, nullable=True)  # 医生修改后的文本
    degraded_output = Column(Boolean, default=False)  # 是否降级输出
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 关系
    report = relationship("Report", back_populates="review_task")
    doctor = relationship("User", back_populates="review_tasks")

    def __repr__(self) -> str:
        return f"<ReviewTask(id={self.id}, status={self.status})>"


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    node_name = Column(String(100), nullable=False)  # 智能体节点名称
    action = Column(String(100), nullable=False)  # 操作类型
    input_data = Column(JSON, nullable=True)  # 输入数据
    output_data = Column(JSON, nullable=True)  # 输出数据
    input_hash = Column(String(64), nullable=True)  # 输入数据哈希
    output_hash = Column(String(64), nullable=True)  # 输出数据哈希
    duration_ms = Column(Integer, nullable=True)  # 执行耗时(毫秒)
    status = Column(
        Enum("success", "error", "timeout", name="audit_status"),
        default="success",
    )
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, node={self.node_name}, action={self.action})>"


class KnowledgeBase(Base):
    """知识库表"""
    __tablename__ = "knowledge_bases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(
        Enum("symptom", "guideline", "general", name="kb_type"),
        nullable=False,
    )
    document_count = Column(Integer, default=0)
    status = Column(
        Enum("active", "inactive", "building", name="kb_status"),
        default="active",
    )
    config = Column(JSON, nullable=True)  # 知识库配置参数
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<KnowledgeBase(id={self.id}, name={self.name}, type={self.type})>"


class Document(Base):
    """文档表"""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    knowledge_base_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False)
    title = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    file_type = Column(String(50), nullable=True)
    chunk_count = Column(Integer, default=0)
    status = Column(
        Enum("pending", "processing", "completed", "failed", name="doc_status"),
        default="pending",
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title})>"
