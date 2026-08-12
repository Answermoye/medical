"""
医疗导诊与报告解读助手 - 检验指标结构化查询模块

封装MySQL检验指标参考值的CRUD操作
"""

from typing import Any, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from backend.core.logger import setup_logger
from backend.db.models import Base

logger = setup_logger(__name__)


class LabReferenceValue(Base):
    """检验指标参考值模型"""
    __tablename__ = "lab_reference_values"

    from sqlalchemy import Column, String, Float, Integer, Text, Boolean
    from sqlalchemy.sql import func
    from datetime import datetime

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_name = Column(String(100), nullable=False, index=True, comment="检验项目名称")
    item_name_en = Column(String(100), nullable=True, comment="检验项目英文名")
    category = Column(String(50), nullable=False, comment="检验类别")
    unit = Column(String(50), nullable=False, comment="单位")
    reference_range_low = Column(Float, nullable=True, comment="参考范围下限")
    reference_range_high = Column(Float, nullable=True, comment="参考范围上限")
    reference_range_text = Column(String(200), nullable=True, comment="参考范围文本描述")
    clinical_significance = Column(Text, nullable=True, comment="临床意义")
    abnormal_high_meaning = Column(Text, nullable=True, comment="偏高含义")
    abnormal_low_meaning = Column(Text, nullable=True, comment="偏低含义")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(String(50), default=str(datetime.now()), comment="创建时间")
    updated_at = Column(String(50), default=str(datetime.now()), comment="更新时间")

    def __repr__(self) -> str:
        return f"<LabReferenceValue(item_name={self.item_name}, category={self.category})>"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "item_name": self.item_name,
            "item_name_en": self.item_name_en,
            "category": self.category,
            "unit": self.unit,
            "reference_range_low": self.reference_range_low,
            "reference_range_high": self.reference_range_high,
            "reference_range_text": self.reference_range_text,
            "clinical_significance": self.clinical_significance,
            "abnormal_high_meaning": self.abnormal_high_meaning,
            "abnormal_low_meaning": self.abnormal_low_meaning,
        }


class LabValueDB:
    """检验指标数据库操作类"""

    def __init__(self, db: Session):
        """
        初始化

        Args:
            db: 数据库会话
        """
        self.db = db

    def get_by_name(self, item_name: str) -> LabReferenceValue | None:
        """
        根据项目名称查询参考值

        Args:
            item_name: 检验项目名称

        Returns:
            参考值对象或None
        """
        # 精确匹配
        result = self.db.query(LabReferenceValue).filter(
            and_(
                LabReferenceValue.item_name == item_name,
                LabReferenceValue.is_active == True,
            )
        ).first()

        if result:
            return result

        # 模糊匹配
        result = self.db.query(LabReferenceValue).filter(
            and_(
                LabReferenceValue.item_name.like(f"%{item_name}%"),
                LabReferenceValue.is_active == True,
            )
        ).first()

        return result

    def get_by_name_en(self, item_name_en: str) -> LabReferenceValue | None:
        """
        根据英文名查询参考值

        Args:
            item_name_en: 检验项目英文名

        Returns:
            参考值对象或None
        """
        result = self.db.query(LabReferenceValue).filter(
            and_(
                LabReferenceValue.item_name_en == item_name_en,
                LabReferenceValue.is_active == True,
            )
        ).first()

        return result

    def batch_query(self, item_names: list[str]) -> list[LabReferenceValue]:
        """
        批量查询检验指标

        Args:
            item_names: 项目名称列表

        Returns:
            参考值列表
        """
        results = []
        for item_name in item_names:
            result = self.get_by_name(item_name)
            if result:
                results.append(result)
        return results

    def get_by_category(self, category: str) -> list[LabReferenceValue]:
        """
        根据类别查询检验指标

        Args:
            category: 检验类别

        Returns:
            参考值列表
        """
        return self.db.query(LabReferenceValue).filter(
            and_(
                LabReferenceValue.category == category,
                LabReferenceValue.is_active == True,
            )
        ).all()

    def search(self, keyword: str) -> list[LabReferenceValue]:
        """
        搜索检验指标

        Args:
            keyword: 搜索关键词

        Returns:
            参考值列表
        """
        return self.db.query(LabReferenceValue).filter(
            and_(
                or_(
                    LabReferenceValue.item_name.like(f"%{keyword}%"),
                    LabReferenceValue.item_name_en.like(f"%{keyword}%"),
                    LabReferenceValue.category.like(f"%{keyword}%"),
                ),
                LabReferenceValue.is_active == True,
            )
        ).all()

    def check_abnormal(self, item_name: str, value: float) -> dict[str, Any] | None:
        """
        检查检验值是否异常

        Args:
            item_name: 项目名称
            value: 检验值

        Returns:
            异常信息字典或None
        """
        ref = self.get_by_name(item_name)
        if not ref:
            return None

        result = {
            "item_name": ref.item_name,
            "value": value,
            "unit": ref.unit,
            "reference_range": ref.reference_range_text,
            "is_abnormal": False,
            "abnormal_type": None,  # "high" or "low"
            "meaning": None,
        }

        # 检查是否异常
        if ref.reference_range_low is not None and value < ref.reference_range_low:
            result["is_abnormal"] = True
            result["abnormal_type"] = "low"
            result["meaning"] = ref.abnormal_low_meaning
        elif ref.reference_range_high is not None and value > ref.reference_range_high:
            result["is_abnormal"] = True
            result["abnormal_type"] = "high"
            result["meaning"] = ref.abnormal_high_meaning

        return result

    def batch_check_abnormal(
        self, lab_values: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        批量检查检验值是否异常

        Args:
            lab_values: 检验值列表，格式: [{"item_name": "...", "value": 123}, ...]

        Returns:
            异常信息列表
        """
        results = []
        for lab_value in lab_values:
            item_name = lab_value.get("item_name")
            value = lab_value.get("value")

            if item_name and value is not None:
                result = self.check_abnormal(item_name, float(value))
                if result:
                    results.append(result)

        return results

    def get_all_categories(self) -> list[str]:
        """
        获取所有检验类别

        Returns:
            类别列表
        """
        categories = self.db.query(LabReferenceValue.category).distinct().all()
        return [cat[0] for cat in categories]

    def count(self) -> int:
        """
        统计记录数

        Returns:
            记录数
        """
        return self.db.query(LabReferenceValue).filter(
            LabReferenceValue.is_active == True
        ).count()


def get_lab_value_db(db: Session) -> LabValueDB:
    """
    获取LabValueDB实例

    Args:
        db: 数据库会话

    Returns:
        LabValueDB实例
    """
    return LabValueDB(db)
