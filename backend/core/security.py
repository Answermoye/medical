"""
医疗导诊与报告解读助手 - 密码安全模块

解决passlib与新版bcrypt的兼容性问题
"""

import bcrypt

from backend.core.logger import setup_logger

logger = setup_logger(__name__)


def hash_password(password: str) -> str:
    """
    对密码进行bcrypt哈希

    Args:
        password: 原始密码

    Returns:
        哈希后的密码字符串
    """
    # 截断到72字节（bcrypt限制）
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配

    Args:
        password: 原始密码
        hashed_password: 哈希后的密码

    Returns:
        是否匹配
    """
    try:
        # 截断到72字节（bcrypt限制）
        password_bytes = password.encode("utf-8")[:72]
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"密码验证失败: {e}")
        return False
