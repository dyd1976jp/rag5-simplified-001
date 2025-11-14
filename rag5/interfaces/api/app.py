"""
FastAPI 应用创建和配置。

本模块负责创建和配置 FastAPI 应用实例，注册路由和中间件。
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from .kb_routes import kb_router, set_kb_manager
from rag5.core.knowledge_base import KnowledgeBaseManager
from rag5.tools.vectordb import QdrantManager
from rag5.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器

    在应用启动时初始化 KB Manager,在应用关闭时进行清理。
    """
    logger.info("正在初始化知识库管理器...")

    try:
        # 确保数据目录存在
        data_dir = Path("./data")
        data_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 Qdrant 管理器
        qdrant_manager = QdrantManager(url=settings.qdrant_url)
        logger.info(f"Qdrant 管理器已连接到: {settings.qdrant_url}")

        # 初始化知识库管理器
        kb_manager = KnowledgeBaseManager(
            db_path="./data/knowledge_bases.db",
            qdrant_manager=qdrant_manager,
            file_storage_path="./docs",
            embedding_dimension=settings.vector_dim
        )

        # 从数据库加载知识库到缓存
        count = await kb_manager.initialize()
        logger.info(f"知识库管理器初始化成功,加载了 {count} 个知识库")

        # 设置全局 KB Manager
        set_kb_manager(kb_manager)
        logger.info("全局知识库管理器已设置")

        yield

        # 应用关闭时的清理逻辑
        logger.info("正在关闭知识库管理器...")

    except Exception as e:
        logger.error(f"初始化知识库管理器失败: {e}", exc_info=True)
        raise


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
    # 创建 FastAPI 应用实例,使用 lifespan 管理器
    app = FastAPI(
        title="Simple RAG API",
        description="REST API for RAG5 Simplified System with query optimization and vector search",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
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
