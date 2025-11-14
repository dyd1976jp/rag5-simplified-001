"""
FastAPI 应用创建和配置。

本模块负责创建和配置 FastAPI 应用实例，注册路由和中间件。
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from .kb_routes import kb_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用。

    Returns:
        配置好的 FastAPI 应用实例

    Example:
        >>> app = create_app()
        >>> # 使用 uvicorn 运行
        >>> import uvicorn
        >>> uvicorn.run(app, host="localhost", port=8000)
    """
    # 创建 FastAPI 应用实例
    app = FastAPI(
        title="Simple RAG API",
        description="REST API for RAG5 Simplified System with query optimization and vector search",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 添加 CORS 中间件（如果需要跨域访问）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境中应该限制具体的域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(router, prefix="/api/v1", tags=["chat"])
    app.include_router(kb_router, prefix="/api/v1")

    # 添加根路径端点
    @app.get("/", tags=["root"])
    async def root():
        """根路径，返回 API 信息"""
        return {
            "name": "Simple RAG API",
            "version": "2.0.0",
            "docs": "/docs",
            "health": "/api/v1/health"
        }

    logger.info("FastAPI application created successfully")

    return app


# 创建应用实例（用于直接导入）
app = create_app()


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting FastAPI server on http://localhost:8000")
    uvicorn.run(app, host="localhost", port=8000)
