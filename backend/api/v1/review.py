"""
医生审核相关API
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.logger import setup_logger
from backend.dependencies import get_current_doctor, get_db
from backend.db.models import Report, ReviewTask, User

logger = setup_logger(__name__)
router = APIRouter()


class ReviewAction(BaseModel):
    """审核操作"""
    comment: str = ""
    modified_text: str = ""


@router.get("/pending")
async def get_pending_reviews(
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """获取待审核列表"""
    reviews = (
        db.query(ReviewTask)
        .filter(ReviewTask.status == "pending")
        .order_by(ReviewTask.created_at.asc())
        .all()
    )

    result = []
    for review in reviews:
        report = db.query(Report).filter(Report.id == review.report_id).first()
        result.append({
            "id": review.id,
            "report_id": review.report_id,
            "doctor_id": review.doctor_id,
            "status": review.status,
            "ai_interpretation": review.ai_interpretation,
            "report_title": report.title if report else None,
            "abnormal_items": report.abnormal_items if report else None,
            "risk_level": report.risk_level if report else None,
            "created_at": review.created_at.isoformat(),
        })

    return result


@router.get("/{review_id}")
async def get_review_detail(
    review_id: str,
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """获取审核详情"""
    review = db.query(ReviewTask).filter(ReviewTask.id == review_id).first()

    if not review:
        return {"detail": "审核任务不存在"}

    report = db.query(Report).filter(Report.id == review.report_id).first()

    return {
        "id": review.id,
        "report_id": review.report_id,
        "doctor_id": review.doctor_id,
        "status": review.status,
        "ai_interpretation": review.ai_interpretation,
        "doctor_comment": review.doctor_comment,
        "doctor_modified_text": review.doctor_modified_text,
        "report": {
            "id": report.id if report else None,
            "title": report.title if report else None,
            "image_path": report.image_path if report else None,
            "ocr_raw_data": report.ocr_raw_data if report else None,
            "abnormal_items": report.abnormal_items if report else None,
            "risk_level": report.risk_level if report else None,
            "interpretation": report.interpretation if report else None,
        },
        "created_at": review.created_at.isoformat(),
    }


@router.post("/{review_id}/approve")
async def approve_review(
    review_id: str,
    action: ReviewAction = ReviewAction(),
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """批准审核"""
    review = db.query(ReviewTask).filter(ReviewTask.id == review_id).first()

    if not review:
        return {"detail": "审核任务不存在"}

    if review.status != "pending":
        return {"detail": "该审核任务已处理"}

    review.status = "approved"
    review.doctor_id = current_user.id
    review.doctor_comment = action.comment
    review.completed_at = datetime.utcnow()
    db.commit()

    logger.info(f"审核 {review_id} 已批准")

    return {"message": "审核已通过", "status": "approved"}


@router.post("/{review_id}/modify")
async def modify_review(
    review_id: str,
    action: ReviewAction = ReviewAction(),
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """修改审核"""
    review = db.query(ReviewTask).filter(ReviewTask.id == review_id).first()

    if not review:
        return {"detail": "审核任务不存在"}

    if review.status != "pending":
        return {"detail": "该审核任务已处理"}

    if not action.modified_text:
        return {"detail": "请提供修改后的文本"}

    review.status = "modified"
    review.doctor_id = current_user.id
    review.doctor_comment = action.comment
    review.doctor_modified_text = action.modified_text
    review.completed_at = datetime.utcnow()

    # 同步更新报告的解读内容
    report = db.query(Report).filter(Report.id == review.report_id).first()
    if report:
        report.interpretation = action.modified_text

    db.commit()

    logger.info(f"审核 {review_id} 已修改")

    return {"message": "审核已修改", "status": "modified"}


@router.post("/{review_id}/reject")
async def reject_review(
    review_id: str,
    action: ReviewAction = ReviewAction(),
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """驳回审核"""
    review = db.query(ReviewTask).filter(ReviewTask.id == review_id).first()

    if not review:
        return {"detail": "审核任务不存在"}

    if review.status != "pending":
        return {"detail": "该审核任务已处理"}

    review.status = "rejected"
    review.doctor_id = current_user.id
    review.doctor_comment = action.comment
    review.completed_at = datetime.utcnow()
    db.commit()

    logger.info(f"审核 {review_id} 已驳回")

    return {"message": "审核已驳回", "status": "rejected"}
