"""
医疗导诊与报告解读助手 - 数据库迁移模块

使用Alembic管理数据库版本迁移
"""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from backend.config import get_settings
from backend.core.logger import setup_logger
from backend.db.models import Base

logger = setup_logger(__name__)


class MigrationManager:
    """数据库迁移管理器"""

    def __init__(self):
        self.settings = get_settings()
        self.alembic_cfg: Config | None = None

    def init_alembic(self, migrations_dir: str = "migrations") -> None:
        """
        初始化Alembic配置

        Args:
            migrations_dir: 迁移脚本目录
        """
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        migrations_path = project_root / migrations_dir

        # 创建迁移目录
        migrations_path.mkdir(exist_ok=True)
        (migrations_path / "versions").mkdir(exist_ok=True)

        # 创建alembic.ini
        alembic_ini_path = project_root / "alembic.ini"
        if not alembic_ini_path.exists():
            self._create_alembic_ini(alembic_ini_path, migrations_path)

        # 创建env.py
        env_py_path = migrations_path / "env.py"
        if not env_py_path.exists():
            self._create_env_py(env_py_path)

        # 创建script.py.mako
        script_mako_path = migrations_path / "script.py.mako"
        if not script_mako_path.exists():
            self._create_script_mako(script_mako_path)

        # 初始化Alembic配置
        self.alembic_cfg = Config(str(alembic_ini_path))
        self.alembic_cfg.set_main_option("script_location", str(migrations_path))

        logger.info(f"Alembic初始化完成: {migrations_path}")

    def _create_alembic_ini(self, path: Path, migrations_path: Path) -> None:
        """创建alembic.ini文件"""
        content = f"""# Alembic Configuration File

[alembic]
script_location = {migrations_path}
prepend_sys_path = .
sqlalchemy.url = {self.settings.DATABASE_URL}

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        path.write_text(content, encoding="utf-8")

    def _create_env_py(self, path: Path) -> None:
        """创建env.py文件"""
        content = """from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from backend.config import get_settings
from backend.db.models import Base

# Alembic Config对象
config = context.config

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置MetaData
target_metadata = Base.metadata

# 获取数据库URL
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """离线模式运行迁移"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式运行迁移"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""
        path.write_text(content, encoding="utf-8")

    def _create_script_mako(self, path: Path) -> None:
        """创建script.py.mako文件"""
        content = """\"\"\"${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

\"\"\"
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
"""
        path.write_text(content, encoding="utf-8")

    def create_migration(self, message: str) -> str:
        """
        创建迁移脚本

        Args:
            message: 迁移说明

        Returns:
            迁移脚本路径
        """
        if not self.alembic_cfg:
            self.init_alembic()

        try:
            revision = command.revision(self.alembic_cfg, message=message, autogenerate=True)
            logger.info(f"创建迁移脚本: {message}")
            return str(revision)
        except Exception as e:
            logger.error(f"创建迁移脚本失败: {e}")
            raise

    def upgrade(self, revision: str = "head") -> None:
        """
        执行迁移

        Args:
            revision: 目标版本，默认为最新版本
        """
        if not self.alembic_cfg:
            self.init_alembic()

        try:
            command.upgrade(self.alembic_cfg, revision)
            logger.info(f"数据库迁移到版本: {revision}")
        except Exception as e:
            logger.error(f"数据库迁移失败: {e}")
            raise

    def downgrade(self, revision: str) -> None:
        """
        回滚迁移

        Args:
            revision: 目标版本
        """
        if not self.alembic_cfg:
            self.init_alembic()

        try:
            command.downgrade(self.alembic_cfg, revision)
            logger.info(f"数据库回滚到版本: {revision}")
        except Exception as e:
            logger.error(f"数据库回滚失败: {e}")
            raise

    def get_current_revision(self) -> str | None:
        """
        获取当前数据库版本

        Returns:
            当前版本号或None
        """
        engine = create_engine(self.settings.DATABASE_URL)

        try:
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                return context.get_current_revision()
        except Exception as e:
            logger.warning(f"获取数据库版本失败: {e}")
            return None

    def check_tables_exist(self) -> dict[str, bool]:
        """
        检查表是否存在

        Returns:
            表名和存在状态的字典
        """
        engine = create_engine(self.settings.DATABASE_URL)
        inspector = inspect(engine)

        existing_tables = inspector.get_table_names()
        expected_tables = [table.name for table in Base.metadata.tables.values()]

        return {
            table: table in existing_tables
            for table in expected_tables
        }

    def create_tables(self) -> None:
        """直接创建所有表（开发环境使用）"""
        engine = create_engine(self.settings.DATABASE_URL)

        try:
            Base.metadata.create_all(engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"数据库表创建失败: {e}")
            raise

    def drop_tables(self) -> None:
        """删除所有表（开发环境使用）"""
        engine = create_engine(self.settings.DATABASE_URL)

        try:
            Base.metadata.drop_all(engine)
            logger.info("数据库表删除成功")
        except Exception as e:
            logger.error(f"数据库表删除失败: {e}")
            raise


# 全局MigrationManager实例
migration_manager = MigrationManager()
