"""
数据库初始化脚本

创建测试用户和示例数据
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import get_settings
from backend.core.logger import setup_logger
from backend.core.security import hash_password
from backend.db.models import Base, User, KnowledgeBase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = setup_logger(__name__)


def init_database():
    """初始化数据库"""
    settings = get_settings()

    # 创建数据库引擎
    engine = create_engine(settings.DATABASE_URL)

    # 创建所有表
    logger.info("创建数据库表...")
    Base.metadata.create_all(engine)
    logger.info("数据库表创建完成")

    # 创建会话
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 创建测试用户
        create_test_users(db)

        # 创建示例知识库
        create_sample_knowledge_bases(db)

        logger.info("数据库初始化完成！")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_test_users(db):
    """创建测试用户"""
    logger.info("创建测试用户...")

    users_data = [
        {
            "username": "admin",
            "password": "admin123",
            "role": "admin",
        },
        {
            "username": "doctor1",
            "password": "doctor123",
            "role": "doctor",
        },
        {
            "username": "patient1",
            "password": "patient123",
            "role": "patient",
        },
    ]

    for user_data in users_data:
        # 检查用户是否已存在
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if existing:
            logger.info(f"用户 {user_data['username']} 已存在，跳过")
            continue

        user = User(
            username=user_data["username"],
            password_hash=hash_password(user_data["password"]),
            role=user_data["role"],
        )
        db.add(user)
        logger.info(f"创建用户: {user_data['username']} ({user_data['role']})")

    db.commit()
    logger.info("测试用户创建完成")


def create_sample_knowledge_bases(db):
    """创建示例知识库"""
    logger.info("创建示例知识库...")

    kbs_data = [
        {
            "name": "症状科室映射库",
            "description": "包含常见症状与对应科室的映射关系",
            "type": "symptom",
        },
        {
            "name": "医学指南库",
            "description": "包含常见疾病的诊疗指南和医学科普",
            "type": "guideline",
        },
        {
            "name": "通用健康知识库",
            "description": "包含健康生活方式、饮食运动等通用知识",
            "type": "general",
        },
    ]

    for kb_data in kbs_data:
        # 检查是否已存在
        existing = db.query(KnowledgeBase).filter(KnowledgeBase.name == kb_data["name"]).first()
        if existing:
            logger.info(f"知识库 '{kb_data['name']}' 已存在，跳过")
            continue

        kb = KnowledgeBase(
            name=kb_data["name"],
            description=kb_data["description"],
            type=kb_data["type"],
            status="active",
        )
        db.add(kb)
        logger.info(f"创建知识库: {kb_data['name']}")

    db.commit()
    logger.info("示例知识库创建完成")


if __name__ == "__main__":
    init_database()
    print("\n✅ 数据库初始化完成！")
    print("\n测试账号:")
    print("  管理员: admin / admin123")
    print("  医生:   doctor1 / doctor123")
    print("  患者:   patient1 / patient123")
