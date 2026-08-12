"""
报告相关API
"""

import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from backend.core.logger import setup_logger
from backend.dependencies import get_current_user, get_db
from backend.db.models import Report, ReviewTask, User

logger = setup_logger(__name__)
router = APIRouter()


@router.post("/upload")
async def upload_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传报告图片"""
    # 保存文件
    upload_dir = "uploads/reports"
    os.makedirs(upload_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 创建报告记录
    report = Report(
        user_id=current_user.id,
        title=file.filename or "未命名报告",
        image_path=file_path,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # 创建审核任务
    review_task = ReviewTask(
        report_id=report.id,
        status="pending",
    )
    db.add(review_task)
    db.commit()

    return {
        "id": report.id,
        "title": report.title,
        "image_path": report.image_path,
        "status": report.status,
        "created_at": report.created_at.isoformat(),
    }


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取报告详情"""
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.user_id == current_user.id)
        .first()
    )

    if not report:
        return {"detail": "报告不存在"}

    return {
        "id": report.id,
        "user_id": report.user_id,
        "title": report.title,
        "image_path": report.image_path,
        "abnormal_items": report.abnormal_items,
        "risk_level": report.risk_level,
        "interpretation": report.interpretation,
        "status": report.status,
        "created_at": report.created_at.isoformat(),
    }


@router.get("/{report_id}/result")
async def get_report_result(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取报告解读结果"""
    report = (
        db.query(Report)
        .filter(Report.id == report_id)
        .first()
    )

    if not report:
        return {"detail": "报告不存在"}

    # 如果报告还未处理，调用ReportAgent处理
    if report.status == "pending":
        from backend.agents.report_agent import report_agent

        result = await report_agent.process(
            report_id=report.id,
            user_id=current_user.id,
            image_path=report.image_path,
        )

        # 更新报告
        report.ocr_raw_data = result.get("ocr_raw_data", "")
        report.parsed_data = result.get("parsed_lab_values", [])
        report.abnormal_items = result.get("abnormal_items", [])
        report.risk_level = result.get("risk_level", "normal")
        report.interpretation = result.get("interpretation", "")
        report.status = "completed"
        db.commit()

    # 获取审核状态
    review_task = db.query(ReviewTask).filter(ReviewTask.report_id == report_id).first()

    return {
        "id": report.id,
        "abnormal_items": report.abnormal_items,
        "risk_level": report.risk_level,
        "interpretation": report.interpretation,
        "status": report.status,
        "review_status": review_task.status if review_task else None,
    }


@router.get("/user/{user_id}")
async def get_user_reports(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户报告列表"""
    reports = (
        db.query(Report)
        .filter(Report.user_id == user_id)
        .order_by(Report.created_at.desc())
        .all()
    )

    return [
        {
            "id": r.id,
            "title": r.title,
            "risk_level": r.risk_level,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ]
