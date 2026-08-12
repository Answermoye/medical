"""
配置模块测试
"""

import pytest

from backend.config import Settings, get_settings


def test_settings_default_values():
    """测试配置默认值"""
    settings = Settings(
        SECRET_KEY="test-secret-key",
        MYSQL_PASSWORD="test-password",
        DEBUG=False,
        _env_file=None,  # 不加载.env文件
    )

    assert settings.APP_NAME == "医疗导诊与报告解读助手"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.DEBUG is False
    assert settings.MYSQL_HOST == "localhost"
    assert settings.MYSQL_PORT == 3306
    assert settings.REDIS_HOST == "localhost"
    assert settings.REDIS_PORT == 6379
    assert settings.MILVUS_HOST == "localhost"
    assert settings.MILVUS_PORT == 19530


def test_settings_database_url():
    """测试数据库URL构建"""
    settings = Settings(
        SECRET_KEY="test-secret-key",
        MYSQL_HOST="testhost",
        MYSQL_PORT=3307,
        MYSQL_USER="testuser",
        MYSQL_PASSWORD="testpass",
        MYSQL_DATABASE="testdb",
    )

    expected_url = "mysql+pymysql://testuser:testpass@testhost:3307/testdb"
    assert settings.DATABASE_URL == expected_url


def test_settings_redis_url():
    """测试Redis URL构建"""
    settings = Settings(
        SECRET_KEY="test-secret-key",
        REDIS_HOST="redishost",
        REDIS_PORT=6380,
        REDIS_PASSWORD="redispass",
        REDIS_DB=1,
    )

    expected_url = "redis://:redispass@redishost:6380/1"
    assert settings.REDIS_URL == expected_url


def test_settings_redis_url_without_password():
    """测试无密码的Redis URL构建"""
    settings = Settings(
        SECRET_KEY="test-secret-key",
        REDIS_HOST="redishost",
        REDIS_PORT=6380,
        REDIS_PASSWORD=None,
        REDIS_DB=0,
    )

    expected_url = "redis://redishost:6380/0"
    assert settings.REDIS_URL == expected_url


def test_get_settings_returns_singleton():
    """测试get_settings返回单例"""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2
