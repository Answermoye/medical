"""
医疗导诊与报告解读助手 - FastAPI主入口
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.core.logger import setup_logger

# 初始化日志
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    logger.info("正在启动医疗导诊与报告解读助手...")

    # 初始化数据库连接
    # TODO: 初始化数据库引擎和连接池

    # 初始化Redis连接
    # TODO: 初始化Redis客户端

    # 初始化Milvus连接
    # TODO: 初始化Milvus客户端

    logger.info("应用启动完成")

    yield

    # 清理资源
    logger.info("正在关闭应用...")
    # TODO: 关闭数据库连接、Redis连接等
    logger.info("应用已关闭")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="基于多智能体架构的医疗导诊与报告解读系统",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 请求处理时间中间件
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"未处理的异常: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误，请稍后重试"},
        )

    # 注册路由
    register_routers(app)

    # 注册健康检查
    register_health_check(app)

    return app


def register_routers(app: FastAPI) -> None:
    """注册API路由"""
    from backend.api.v1 import auth, chat, knowledge_base, report, review

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["对话"])
    app.include_router(report.router, prefix="/api/v1/report", tags=["报告"])
    app.include_router(review.router, prefix="/api/v1/review", tags=["审核"])
    app.include_router(knowledge_base.router, prefix="/api/v1/knowledge-base", tags=["知识库"])


def register_health_check(app: FastAPI) -> None:
    """注册健康检查端点"""

    @app.get("/health", tags=["系统"])
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "version": get_settings().APP_VERSION,
        }

    @app.get("/", tags=["系统"])
    async def root():
        """根路径"""
        return {
            "message": "欢迎使用医疗导诊与报告解读助手",
            "docs": "/docs",
        }


# 创建应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
