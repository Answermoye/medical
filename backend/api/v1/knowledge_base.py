"""
知识库管理API
"""

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.logger import setup_logger
from backend.dependencies import get_current_admin, get_db
from backend.db.models import Document, KnowledgeBase, User

logger = setup_logger(__name__)
router = APIRouter()


class CreateKBRequest(BaseModel):
    """创建知识库请求"""
    name: str
    description: str = ""
    type: str = "general"


@router.post("/")
async def create_knowledge_base(
    request: CreateKBRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """创建知识库"""
    if request.type not in ["symptom", "guideline", "general"]:
        return {"detail": "无效的知识库类型"}

    kb = KnowledgeBase(
        name=request.name,
        description=request.description,
        type=request.type,
        status="active",
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)

    logger.info(f"知识库 {kb.name} 创建成功")

    return {
        "id": kb.id,
        "name": kb.name,
        "description": kb.description,
        "type": kb.type,
        "document_count": kb.document_count,
        "status": kb.status,
        "created_at": kb.created_at.isoformat(),
    }


@router.get("/")
async def list_knowledge_bases(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """获取知识库列表"""
    kbs = db.query(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()).all()

    return [
        {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "type": kb.type,
            "document_count": kb.document_count,
            "status": kb.status,
            "created_at": kb.created_at.isoformat(),
        }
        for kb in kbs
    ]


@router.get("/{kb_id}")
async def get_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """获取知识库详情"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()

    if not kb:
        return {"detail": "知识库不存在"}

    return {
        "id": kb.id,
        "name": kb.name,
        "description": kb.description,
        "type": kb.type,
        "document_count": kb.document_count,
        "status": kb.status,
        "config": kb.config,
        "created_at": kb.created_at.isoformat(),
    }


@router.post("/{kb_id}/documents")
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """上传文档到知识库"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()

    if not kb:
        return {"detail": "知识库不存在"}

    # 保存文件
    upload_dir = f"uploads/knowledge_base/{kb_id}"
    os.makedirs(upload_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".txt"
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 创建文档记录
    document = Document(
        knowledge_base_id=kb_id,
        title=file.filename or "未命名文档",
        file_path=file_path,
        file_type=file_ext.lstrip("."),
        status="pending",
    )
    db.add(document)

    # 更新文档数
    kb.document_count = (kb.document_count or 0) + 1

    db.commit()
    db.refresh(document)

    logger.info(f"文档 {document.title} 上传成功")

    return {
        "id": document.id,
        "title": document.title,
        "file_type": document.file_type,
        "status": document.status,
        "created_at": document.created_at.isoformat(),
    }


@router.get("/{kb_id}/documents")
async def list_documents(
    kb_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """获取知识库文档列表"""
    documents = (
        db.query(Document)
        .filter(Document.knowledge_base_id == kb_id)
        .order_by(Document.created_at.desc())
        .all()
    )

    return [
        {
            "id": doc.id,
            "title": doc.title,
            "file_type": doc.file_type,
            "chunk_count": doc.chunk_count,
            "status": doc.status,
            "created_at": doc.created_at.isoformat(),
        }
        for doc in documents
    ]


@router.delete("/{kb_id}/documents/{doc_id}")
async def delete_document(
    kb_id: str,
    doc_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除文档"""
    document = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.knowledge_base_id == kb_id)
        .first()
    )

    if not document:
        return {"detail": "文档不存在"}

    # 删除文件
    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)

    # 更新文档数
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if kb:
        kb.document_count = max(0, (kb.document_count or 0) - 1)

    db.delete(document)
    db.commit()

    logger.info(f"文档 {doc_id} 已删除")

    return {"message": "文档已删除"}


@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除知识库"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()

    if not kb:
        return {"detail": "知识库不存在"}

    # 删除关联文档
    documents = db.query(Document).filter(Document.knowledge_base_id == kb_id).all()
    for doc in documents:
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        db.delete(doc)

    db.delete(kb)
    db.commit()

    logger.info(f"知识库 {kb_id} 已删除")

    return {"message": "知识库已删除"}
