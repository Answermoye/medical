"""
数据库模型测试
"""

import pytest
from datetime import datetime

from backend.db.models import (
    AuditLog,
    Document,
    KnowledgeBase,
    Message,
    Report,
    ReviewTask,
    Session,
    User,
    generate_uuid,
)


def test_generate_uuid():
    """测试UUID生成"""
    uuid1 = generate_uuid()
    uuid2 = generate_uuid()

    assert uuid1 != uuid2
    assert len(uuid1) == 36
    assert uuid1.count("-") == 4


def test_user_creation(db_session):
    """测试用户创建"""
    user = User(
        username="testuser",
        password_hash="hashed_password",
        role="patient",
    )
    db_session.add(user)
    db_session.commit()

    saved_user = db_session.query(User).filter(User.username == "testuser").first()
    assert saved_user is not None
    assert saved_user.username == "testuser"
    assert saved_user.role == "patient"
    assert saved_user.is_active is True
    assert saved_user.created_at is not None


def test_session_creation(db_session):
    """测试会话创建"""
    user = User(
        username="testuser",
        password_hash="hashed_password",
        role="patient",
    )
    db_session.add(user)
    db_session.commit()

    session = Session(
        user_id=user.id,
        mode="triage",
        title="测试会话",
    )
    db_session.add(session)
    db_session.commit()

    saved_session = db_session.query(Session).filter(Session.user_id == user.id).first()
    assert saved_session is not None
    assert saved_session.mode == "triage"
    assert saved_session.title == "测试会话"
    assert saved_session.is_active is True


def test_message_creation(db_session):
    """测试消息创建"""
    user = User(
        username="testuser",
        password_hash="hashed_password",
        role="patient",
    )
    db_session.add(user)
    db_session.commit()

    session = Session(
        user_id=user.id,
        mode="general",
    )
    db_session.add(session)
    db_session.commit()

    message = Message(
        session_id=session.id,
        role="user",
        content="你好，我想咨询一下",
    )
    db_session.add(message)
    db_session.commit()

    saved_message = db_session.query(Message).filter(Message.session_id == session.id).first()
    assert saved_message is not None
    assert saved_message.role == "user"
    assert saved_message.content == "你好，我想咨询一下"
    assert saved_message.message_type == "text"


def test_report_creation(db_session):
    """测试报告创建"""
    user = User(
        username="testuser",
        password_hash="hashed_password",
        role="patient",
    )
    db_session.add(user)
    db_session.commit()

    report = Report(
        user_id=user.id,
        title="血常规报告",
        image_path="/uploads/report.jpg",
        status="pending",
    )
    db_session.add(report)
    db_session.commit()

    saved_report = db_session.query(Report).filter(Report.user_id == user.id).first()
    assert saved_report is not None
    assert saved_report.title == "血常规报告"
    assert saved_report.status == "pending"


def test_review_task_creation(db_session):
    """测试审核任务创建"""
    user = User(
        username="testuser",
        password_hash="hashed_password",
        role="patient",
    )
    doctor = User(
        username="doctor",
        password_hash="hashed_password",
        role="doctor",
    )
    db_session.add_all([user, doctor])
    db_session.commit()

    report = Report(
        user_id=user.id,
        title="血常规报告",
        status="completed",
    )
    db_session.add(report)
    db_session.commit()

    review_task = ReviewTask(
        report_id=report.id,
        doctor_id=doctor.id,
        ai_interpretation="AI解读内容",
        status="pending",
    )
    db_session.add(review_task)
    db_session.commit()

    saved_task = db_session.query(ReviewTask).filter(ReviewTask.report_id == report.id).first()
    assert saved_task is not None
    assert saved_task.status == "pending"
    assert saved_task.ai_interpretation == "AI解读内容"


def test_audit_log_creation(db_session):
    """测试审计日志创建"""
    audit_log = AuditLog(
        node_name="TriageAgent",
        action="recommend_department",
        input_data={"symptoms": ["头痛"]},
        output_data={"departments": ["神经内科"]},
        duration_ms=150,
        status="success",
    )
    db_session.add(audit_log)
    db_session.commit()

    saved_log = db_session.query(AuditLog).filter(AuditLog.node_name == "TriageAgent").first()
    assert saved_log is not None
    assert saved_log.action == "recommend_department"
    assert saved_log.duration_ms == 150


def test_knowledge_base_creation(db_session):
    """测试知识库创建"""
    kb = KnowledgeBase(
        name="症状科室映射库",
        description="包含常见症状与对应科室的映射关系",
        type="symptom",
    )
    db_session.add(kb)
    db_session.commit()

    saved_kb = db_session.query(KnowledgeBase).filter(KnowledgeBase.name == "症状科室映射库").first()
    assert saved_kb is not None
    assert saved_kb.type == "symptom"
    assert saved_kb.document_count == 0


def test_document_creation(db_session):
    """测试文档创建"""
    kb = KnowledgeBase(
        name="测试知识库",
        type="guideline",
    )
    db_session.add(kb)
    db_session.commit()

    document = Document(
        knowledge_base_id=kb.id,
        title="高血压诊疗指南",
        file_path="/data/guidelines/hypertension.pdf",
        file_type="pdf",
        status="completed",
    )
    db_session.add(document)
    db_session.commit()

    saved_doc = db_session.query(Document).filter(Document.knowledge_base_id == kb.id).first()
    assert saved_doc is not None
    assert saved_doc.title == "高血压诊疗指南"
    assert saved_doc.file_type == "pdf"
