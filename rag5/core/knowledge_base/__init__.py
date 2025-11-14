"""
知识库管理模块

提供多知识库管理功能，包括：
- 知识库的创建、更新、删除和查询
- 文件上传和管理
- 独立的分块和检索配置
- 向量存储集成
- 内存缓存层提高访问性能
- 数据库初始化和迁移工具

主要组件：
- models: 数据模型（KnowledgeBase, FileEntity, ChunkConfig, RetrievalConfig）
- database: 数据库操作（KnowledgeBaseDatabase）
- provider: 内存缓存层（KnowledgeBaseProvider）
- vector_manager: 向量存储管理（VectorStoreManager）
- manager: 核心管理器（KnowledgeBaseManager）

使用示例：
    >>> from rag5.core.knowledge_base import (
    ...     KnowledgeBase,
    ...     KnowledgeBaseDatabase,
    ...     KnowledgeBaseProvider,
    ...     VectorStoreManager,
    ...     initialize_kb_system
    ... )
    >>> 
    >>> # 初始化知识库系统
    >>> initialize_kb_system()
    >>> 
    >>> # 创建数据库实例
    >>> db = KnowledgeBaseDatabase("./data/kb.db")
    >>> 
    >>> # 创建知识库
    >>> kb = KnowledgeBase(
    ...     id="kb_123",
    ...     name="my_kb",
    ...     description="My knowledge base",
    ...     embedding_model="nomic-embed-text"
    ... )
    >>> db.create_kb(kb)
    >>> 
    >>> # 使用提供者缓存
    >>> provider = KnowledgeBaseProvider()
    >>> await provider.load_from_db(db)
    >>> cached_kb = provider.get("kb_123")

迁移和初始化：
    >>> # 初始化数据库（创建表和索引）
    >>> from rag5.core.knowledge_base import initialize_database
    >>> db = initialize_database("./data/kb.db")
    >>> 
    >>> # 创建默认知识库（用于向后兼容）
    >>> from rag5.core.knowledge_base import create_default_kb
    >>> default_kb = create_default_kb(db)
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from rag5.core.knowledge_base.models import (
    KnowledgeBase,
    FileEntity,
    FileStatus,
    ChunkConfig,
    RetrievalConfig
)
from rag5.core.knowledge_base.database import KnowledgeBaseDatabase
from rag5.core.knowledge_base.provider import KnowledgeBaseProvider
from rag5.core.knowledge_base.vector_manager import VectorStoreManager
from rag5.core.knowledge_base.manager import (
    KnowledgeBaseManager,
    KnowledgeBaseError,
    KnowledgeBaseNotFoundError,
    KnowledgeBaseAlreadyExistsError,
    KnowledgeBaseValidationError,
    FileNotFoundError,
    FileValidationError
)

logger = logging.getLogger(__name__)


def initialize_database(db_path: str) -> KnowledgeBaseDatabase:
    """
    初始化知识库数据库
    
    创建所有必需的表和索引。如果表已存在，则跳过创建。
    这是设置知识库系统的第一步。
    
    参数:
        db_path: 数据库文件路径
    
    返回:
        KnowledgeBaseDatabase 实例
    
    异常:
        Exception: 如果数据库初始化失败
    
    示例:
        >>> db = initialize_database("./data/knowledge_bases.db")
        >>> print("数据库初始化成功")
    """
    logger.info(f"初始化知识库数据库: {db_path}")
    
    try:
        # 创建数据库实例（会自动创建表和索引）
        db = KnowledgeBaseDatabase(db_path)
        logger.info("知识库数据库初始化成功")
        return db
    except Exception as e:
        logger.error(f"知识库数据库初始化失败: {e}", exc_info=True)
        raise


def create_default_kb(
    db: KnowledgeBaseDatabase,
    embedding_model: str = "bge-m3",
    chunk_config: Optional[ChunkConfig] = None,
    retrieval_config: Optional[RetrievalConfig] = None
) -> Optional[KnowledgeBase]:
    """
    创建默认知识库
    
    为向后兼容性创建一个默认知识库。如果默认知识库已存在，则返回现有的。
    这允许现有的单知识库代码继续工作，而无需修改。
    
    参数:
        db: KnowledgeBaseDatabase 实例
        embedding_model: 嵌入模型名称（默认: "bge-m3"）
        chunk_config: 自定义分块配置（可选）
        retrieval_config: 自定义检索配置（可选）
    
    返回:
        创建或已存在的默认知识库，失败时返回 None
    
    示例:
        >>> db = initialize_database("./data/kb.db")
        >>> default_kb = create_default_kb(db, embedding_model="nomic-embed-text")
        >>> print(f"默认知识库 ID: {default_kb.id}")
    """
    logger.info("创建默认知识库...")
    
    try:
        # 检查是否已存在默认知识库
        default_kb_name = "default"
        existing_kb = db.get_kb_by_name(default_kb_name)
        
        if existing_kb:
            logger.info(f"默认知识库已存在 (ID: {existing_kb.id})")
            return existing_kb
        
        # 使用提供的配置或创建默认配置
        if chunk_config is None:
            chunk_config = ChunkConfig(
                chunk_size=512,
                chunk_overlap=50,
                parser_type="sentence",
                separator="\n\n"
            )
        
        if retrieval_config is None:
            retrieval_config = RetrievalConfig(
                retrieval_mode="hybrid",
                top_k=5,
                similarity_threshold=0.3,
                vector_weight=0.5,
                enable_rerank=False,
                rerank_model=""
            )
        
        # 创建默认知识库
        default_kb = KnowledgeBase(
            id=f"kb{uuid.uuid4().hex}",
            name=default_kb_name,
            description="默认知识库 - 用于向后兼容",
            embedding_model=embedding_model,
            chunk_config=chunk_config,
            retrieval_config=retrieval_config,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存到数据库
        db.create_kb(default_kb)
        logger.info(f"默认知识库创建成功 (ID: {default_kb.id})")
        
        return default_kb
        
    except Exception as e:
        logger.error(f"创建默认知识库失败: {e}", exc_info=True)
        return None


def initialize_kb_system(
    db_path: str = "./data/knowledge_bases.db",
    create_default: bool = True,
    embedding_model: str = "bge-m3"
) -> tuple[KnowledgeBaseDatabase, Optional[KnowledgeBase]]:
    """
    初始化完整的知识库系统
    
    这是一个便捷函数，执行以下操作：
    1. 初始化数据库（创建表和索引）
    2. 可选地创建默认知识库（用于向后兼容）
    
    参数:
        db_path: 数据库文件路径（默认: "./data/knowledge_bases.db"）
        create_default: 是否创建默认知识库（默认: True）
        embedding_model: 默认知识库使用的嵌入模型（默认: "bge-m3"）
    
    返回:
        (KnowledgeBaseDatabase 实例, 默认知识库或 None)
    
    异常:
        Exception: 如果数据库初始化失败
    
    示例:
        >>> # 完整初始化
        >>> db, default_kb = initialize_kb_system()
        >>> print(f"系统初始化完成，默认知识库: {default_kb.name}")
        >>> 
        >>> # 仅初始化数据库，不创建默认知识库
        >>> db, _ = initialize_kb_system(create_default=False)
    """
    logger.info("初始化知识库系统...")
    
    # 初始化数据库
    db = initialize_database(db_path)
    
    # 创建默认知识库（如果需要）
    default_kb = None
    if create_default:
        default_kb = create_default_kb(db, embedding_model=embedding_model)
        if default_kb:
            logger.info("知识库系统初始化完成（包含默认知识库）")
        else:
            logger.warning("知识库系统初始化完成（默认知识库创建失败）")
    else:
        logger.info("知识库系统初始化完成（未创建默认知识库）")
    
    return db, default_kb


def get_or_create_default_kb(db: KnowledgeBaseDatabase) -> Optional[KnowledgeBase]:
    """
    获取或创建默认知识库
    
    这是一个便捷函数，用于确保默认知识库存在。
    如果默认知识库已存在，则返回它；否则创建一个新的。
    
    参数:
        db: KnowledgeBaseDatabase 实例
    
    返回:
        默认知识库，失败时返回 None
    
    示例:
        >>> db = KnowledgeBaseDatabase("./data/kb.db")
        >>> default_kb = get_or_create_default_kb(db)
        >>> if default_kb:
        ...     print(f"使用默认知识库: {default_kb.id}")
    """
    try:
        # 尝试获取现有的默认知识库
        default_kb = db.get_kb_by_name("default")
        if default_kb:
            return default_kb
        
        # 如果不存在，创建一个新的
        return create_default_kb(db)
        
    except Exception as e:
        logger.error(f"获取或创建默认知识库失败: {e}", exc_info=True)
        return None


__all__ = [
    # 数据模型
    "KnowledgeBase",
    "FileEntity",
    "FileStatus",
    "ChunkConfig",
    "RetrievalConfig",
    
    # 数据库操作
    "KnowledgeBaseDatabase",
    
    # 缓存层
    "KnowledgeBaseProvider",
    
    # 向量存储管理
    "VectorStoreManager",
    
    # 核心管理器
    "KnowledgeBaseManager",
    
    # 异常类
    "KnowledgeBaseError",
    "KnowledgeBaseNotFoundError",
    "KnowledgeBaseAlreadyExistsError",
    "KnowledgeBaseValidationError",
    "FileNotFoundError",
    "FileValidationError",
    
    # 初始化和迁移工具
    "initialize_database",
    "create_default_kb",
    "initialize_kb_system",
    "get_or_create_default_kb",
]
