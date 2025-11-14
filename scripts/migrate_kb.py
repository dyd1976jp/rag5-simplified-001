#!/usr/bin/env python3
"""
知识库数据库迁移脚本

创建或更新知识库管理所需的数据库表和索引。
支持从单知识库系统迁移到多知识库系统。

使用方法:
    python -m scripts.migrate_kb                    # 基本迁移
    python -m scripts.migrate_kb --create-default   # 创建默认知识库
    python -m scripts.migrate_kb --verify           # 验证迁移结果
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
import uuid

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag5.core.knowledge_base.database import KnowledgeBaseDatabase
from rag5.core.knowledge_base.models import (
    KnowledgeBase,
    ChunkConfig,
    RetrievalConfig
)
from rag5.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_database(db_path: str) -> KnowledgeBaseDatabase:
    """
    初始化知识库数据库
    
    创建所有必需的表和索引。如果表已存在，则跳过创建。
    
    参数:
        db_path: 数据库文件路径
    
    返回:
        KnowledgeBaseDatabase 实例
    
    异常:
        Exception: 如果数据库初始化失败
    """
    logger.info("初始化知识库数据库...")
    logger.info(f"数据库路径: {db_path}")
    
    try:
        # 创建数据库实例（会自动创建表和索引）
        db = KnowledgeBaseDatabase(db_path)
        logger.info("✓ 数据库初始化成功")
        return db
    except Exception as e:
        logger.error(f"✗ 数据库初始化失败: {e}", exc_info=True)
        raise


def verify_database(db_path: str) -> bool:
    """
    验证数据库结构
    
    检查所有必需的表和索引是否存在。
    
    参数:
        db_path: 数据库文件路径
    
    返回:
        验证是否成功
    """
    logger.info("验证数据库结构...")
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查 knowledge_bases 表
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='knowledge_bases'
        """)
        if cursor.fetchone():
            logger.info("✓ knowledge_bases 表存在")
        else:
            logger.error("✗ knowledge_bases 表不存在")
            conn.close()
            return False
        
        # 检查 kb_files 表
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='kb_files'
        """)
        if cursor.fetchone():
            logger.info("✓ kb_files 表存在")
        else:
            logger.error("✗ kb_files 表不存在")
            conn.close()
            return False
        
        # 检查索引
        required_indexes = [
            'idx_kb_files_kb_id',
            'idx_kb_files_status',
            'idx_kb_created_at'
        ]
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index'
        """)
        existing_indexes = [row[0] for row in cursor.fetchall()]
        
        for index_name in required_indexes:
            if index_name in existing_indexes:
                logger.info(f"✓ 索引 {index_name} 存在")
            else:
                logger.warning(f"⚠ 索引 {index_name} 不存在")
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(knowledge_bases)")
        kb_columns = {row[1] for row in cursor.fetchall()}
        required_kb_columns = {
            'id', 'name', 'description', 'embedding_model',
            'chunk_config', 'retrieval_config', 'created_at', 'updated_at'
        }
        
        if required_kb_columns.issubset(kb_columns):
            logger.info("✓ knowledge_bases 表结构正确")
        else:
            missing = required_kb_columns - kb_columns
            logger.error(f"✗ knowledge_bases 表缺少列: {missing}")
            conn.close()
            return False
        
        cursor.execute("PRAGMA table_info(kb_files)")
        file_columns = {row[1] for row in cursor.fetchall()}
        required_file_columns = {
            'id', 'kb_id', 'file_name', 'file_path', 'file_extension',
            'file_size', 'file_md5', 'status', 'failed_reason', 'chunk_count',
            'created_at', 'updated_at', 'metadata'
        }
        
        if required_file_columns.issubset(file_columns):
            logger.info("✓ kb_files 表结构正确")
        else:
            missing = required_file_columns - file_columns
            logger.error(f"✗ kb_files 表缺少列: {missing}")
            conn.close()
            return False
        
        conn.close()
        logger.info("✓ 数据库结构验证通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 数据库验证失败: {e}", exc_info=True)
        return False


def create_default_knowledge_base(db: KnowledgeBaseDatabase) -> bool:
    """
    创建默认知识库
    
    为向后兼容性创建一个默认知识库，使用系统配置的默认值。
    如果默认知识库已存在，则跳过创建。
    
    参数:
        db: KnowledgeBaseDatabase 实例
    
    返回:
        是否成功创建或已存在
    """
    logger.info("创建默认知识库...")
    
    try:
        # 检查是否已存在默认知识库
        default_kb_name = "default"
        existing_kb = db.get_kb_by_name(default_kb_name)
        
        if existing_kb:
            logger.info(f"✓ 默认知识库已存在 (ID: {existing_kb.id})")
            return True
        
        # 从配置获取默认值
        embedding_model = getattr(settings, 'embed_model', 'bge-m3')
        
        # 创建默认分块配置
        chunk_config = ChunkConfig(
            chunk_size=getattr(settings, 'kb_chunk_size', 512),
            chunk_overlap=getattr(settings, 'kb_chunk_overlap', 50),
            parser_type=getattr(settings, 'kb_parser_type', 'sentence'),
            separator=getattr(settings, 'kb_separator', '\n\n')
        )
        
        # 创建默认检索配置
        retrieval_config = RetrievalConfig(
            retrieval_mode=getattr(settings, 'kb_retrieval_mode', 'hybrid'),
            top_k=getattr(settings, 'kb_top_k', 5),
            similarity_threshold=getattr(settings, 'kb_similarity_threshold', 0.3),
            vector_weight=getattr(settings, 'kb_vector_weight', 0.5),
            enable_rerank=getattr(settings, 'kb_enable_rerank', False),
            rerank_model=getattr(settings, 'kb_rerank_model', '')
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
        logger.info(f"✓ 默认知识库创建成功 (ID: {default_kb.id})")
        logger.info(f"  - 名称: {default_kb.name}")
        logger.info(f"  - 嵌入模型: {default_kb.embedding_model}")
        logger.info(f"  - 分块大小: {default_kb.chunk_config.chunk_size}")
        logger.info(f"  - 检索模式: {default_kb.retrieval_config.retrieval_mode}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 创建默认知识库失败: {e}", exc_info=True)
        return False


def migrate(create_default: bool = False, verify_only: bool = False) -> bool:
    """
    执行数据库迁移
    
    参数:
        create_default: 是否创建默认知识库
        verify_only: 是否仅验证不执行迁移
    
    返回:
        迁移是否成功
    """
    logger.info("=" * 60)
    logger.info("知识库数据库迁移工具")
    logger.info("=" * 60)
    
    # 获取数据库路径
    db_path = getattr(settings, 'kb_database_path', './data/knowledge_bases.db')
    
    try:
        if verify_only:
            # 仅验证模式
            logger.info("运行验证模式...")
            return verify_database(db_path)
        
        # 初始化数据库
        db = initialize_database(db_path)
        
        # 验证数据库结构
        if not verify_database(db_path):
            logger.error("✗ 数据库结构验证失败")
            return False
        
        # 创建默认知识库（如果需要）
        if create_default:
            if not create_default_knowledge_base(db):
                logger.warning("⚠ 默认知识库创建失败，但迁移继续")
        
        logger.info("=" * 60)
        logger.info("✓ 迁移完成")
        logger.info("=" * 60)
        
        # 显示统计信息
        kbs, total = db.list_kbs(offset=0, limit=100)
        logger.info(f"当前知识库数量: {total}")
        if total > 0:
            logger.info("知识库列表:")
            for kb in kbs:
                logger.info(f"  - {kb.name} (ID: {kb.id})")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 迁移失败: {e}", exc_info=True)
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="知识库数据库迁移工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本迁移（创建表和索引）
  python -m scripts.migrate_kb
  
  # 迁移并创建默认知识库
  python -m scripts.migrate_kb --create-default
  
  # 仅验证数据库结构
  python -m scripts.migrate_kb --verify
        """
    )
    
    parser.add_argument(
        '--create-default',
        action='store_true',
        help='创建默认知识库（用于向后兼容）'
    )
    
    parser.add_argument(
        '--verify',
        action='store_true',
        help='仅验证数据库结构，不执行迁移'
    )
    
    args = parser.parse_args()
    
    success = migrate(
        create_default=args.create_default,
        verify_only=args.verify
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
