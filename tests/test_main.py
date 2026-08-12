"""
主应用测试
"""

import pytest

from backend.main import app


def test_health_check(client):
    """测试健康检查端点"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root(client):
    """测试根路径"""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["docs"] == "/docs"


def test_app_has_cors_middleware():
    """测试应用配置了CORS中间件"""
    middleware_names = [middleware.cls.__name__ for middleware in app.user_middleware]
    assert "CORSMiddleware" in middleware_names
