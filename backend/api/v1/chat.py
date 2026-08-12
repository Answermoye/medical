"""
对话相关API
"""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.agents.router_agent import IntentType
from backend.core.logger import setup_logger
from backend.core.orchestrator import orchestrator
from backend.dependencies import get_current_user, get_db
from backend.db.models import Message, Session as DBSession, User

logger = setup_logger(__name__)
router = APIRouter()


class CreateSessionRequest(BaseModel):
    mode: str


@router.post("/sessions")
async def create_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建会话"""
    session = DBSession(
        user_id=current_user.id,
        mode=request.mode,
        title=f"{request.mode}会话 - {datetime.now().strftime('%m-%d %H:%M')}",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "id": session.id,
        "user_id": session.user_id,
        "mode": session.mode,
        "title": session.title,
        "is_active": session.is_active,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }


@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取会话列表"""
    sessions = (
        db.query(DBSession)
        .filter(DBSession.user_id == current_user.id, DBSession.is_active == True)
        .order_by(DBSession.created_at.desc())
        .all()
    )

    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "mode": s.mode,
            "title": s.title,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取会话详情"""
    session = (
        db.query(DBSession)
        .filter(DBSession.id == session_id, DBSession.user_id == current_user.id)
        .first()
    )

    if not session:
        return {"detail": "会话不存在"}

    return {
        "id": session.id,
        "user_id": session.user_id,
        "mode": session.mode,
        "title": session.title,
        "is_active": session.is_active,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取消息列表"""
    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return [
        {
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role,
            "content": m.content,
            "message_type": m.message_type,
            "metadata": m.extra_data,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    content: str = Form(...),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发送消息"""
    # 保存用户消息
    user_message = Message(
        session_id=session_id,
        role="user",
        content=content,
        message_type="image" if image else "text",
    )
    db.add(user_message)
    db.commit()

    # 处理图片
    image_path = None
    if image:
        import os
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        image_path = os.path.join(upload_dir, f"{session_id}_{image.filename}")
        with open(image_path, "wb") as f:
            f.write(await image.read())

    # 获取对话历史
    history_messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in history_messages
    ]

    # 调用编排器
    result = await orchestrator.process(
        user_input=content,
        user_id=current_user.id,
        session_id=session_id,
        image_path=image_path,
        conversation_history=conversation_history,
    )

    # 保存AI回复
    ai_message = Message(
        session_id=session_id,
        role="assistant",
        content=result.get("response", ""),
    )
    db.add(ai_message)
    db.commit()

    return {
        "message": result.get("response", ""),
        "intent": result.get("intent"),
        "metadata": result.get("metadata", {}),
    }


@router.post("/sessions/{session_id}/messages/stream")
async def stream_message(
    session_id: str,
    content: str = Form(...),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SSE流式发送消息"""

    async def event_generator():
        # 保存用户消息
        user_message = Message(
            session_id=session_id,
            role="user",
            content=content,
            message_type="image" if image else "text",
        )
        db.add(user_message)
        db.commit()

        # 处理图片
        image_path = None
        if image:
            import os
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            image_path = os.path.join(upload_dir, f"{session_id}_{image.filename}")
            with open(image_path, "wb") as f:
                f.write(await image.read())

        # 获取对话历史
        history_messages = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .all()
        )
        conversation_history = [
            {"role": m.role, "content": m.content}
            for m in history_messages
        ]

        # 调用编排器
        result = await orchestrator.process(
            user_input=content,
            user_id=current_user.id,
            session_id=session_id,
            image_path=image_path,
            conversation_history=conversation_history,
        )

        response_text = result.get("response", "")

        # 流式输出
        for char in response_text:
            yield f"data: {json.dumps({'type': 'text', 'content': char})}\n\n"

        # 保存AI回复
        ai_message = Message(
            session_id=session_id,
            role="assistant",
            content=response_text,
        )
        db.add(ai_message)
        db.commit()

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
