"""
认证相关API
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.logger import setup_logger
from backend.core.security import hash_password, verify_password
from backend.dependencies import create_access_token, get_current_user, get_db
from backend.db.models import User

logger = setup_logger(__name__)
router = APIRouter()


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    password: str
    confirm_password: str
    role: str = "patient"


@router.post("/login")
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """用户登录"""
    user = db.query(User).filter(User.username == request.username).first()

    if not user or not verify_password(request.password, user.password_hash):
        return {"detail": "用户名或密码错误"}

    if not user.is_active:
        return {"detail": "用户已被禁用"}

    # 创建token
    access_token = create_access_token(user.id)

    logger.info(f"用户 {user.username} 登录成功")

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/register")
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """用户注册"""
    # 验证密码
    if request.password != request.confirm_password:
        return {"detail": "两次输入的密码不一致"}

    if len(request.password) < 6:
        return {"detail": "密码至少6个字符"}

    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        return {"detail": "用户名已存在"}

    # 验证角色
    if request.role not in ["patient", "doctor"]:
        return {"detail": "无效的角色"}

    # 创建用户
    user = User(
        username=request.username,
        password_hash=hash_password(request.password),
        role=request.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"用户 {user.username} 注册成功")

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """获取当前用户信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "email": current_user.email,
        "phone": current_user.phone,
        "is_active": current_user.is_active,
    }
