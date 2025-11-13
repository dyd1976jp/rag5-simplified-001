"""
测试知识库初始化和迁移工具

测试 initialize_database, create_default_kb, initialize_kb_system 等函数。
"""

import pytest
import tempfile
import os
from pathlib import Path

from rag5.core.knowledge_base import (
    initialize_database,
    create_default_kb,
    initialize_kb_system,
    get_or_create_default_kb,
    KnowledgeBaseDatabase,
    ChunkConfig,
    RetrievalConfig,
)


class TestInitialization:
    """测试数据库初始化功能"""
    
    def test_initialize_database(self):
        """测试 initialize_database 函数"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_kb.db")
            
            # 初始化数据库
            db = initialize_database(db_path)
            
            # 验证数据库实例
            assert isinstance(db, KnowledgeBaseDatabase)
            assert os.path.exists(db_path)
            
            # 验证可以执行基本操作
            kbs, total = db.list_kbs()
            assert total == 0
    
    def test_initialize_database_creates_tables(self):
        """测试数据库表是否正确创建"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_kb.db")
            
            # 初始化数据库
            initialize_database(db_path)
            
            # 验证表存在
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查 knowledge_bases 表
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='knowledge_bases'
            """)
            assert cursor.fetchone() is not None
            
            # 检查 kb_files 表
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='kb_files'
            """)
            assert cursor.fetchone() is not None
            
            conn.close()
    
    def test_create_default_kb(self):
        """测试 create_default_kb 函数"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_kb.db")
            
            # 初始化数据库
            db = initialize_database(db_path)
            
            # 创建默认知识库
            default_kb = create_default_kb(
                db=db,
                embedding_model="test-model"
            )
            
            # 验证默认知识库
            assert default_kb is not None
            assert default_kb.name == "default"
            assert default_kb.embedding_model == "test-model"
            assert default_kb.chunk_config.chunk_size == 512
            assert default_kb.retrieval_config.top_k == 5
    
    def test_create_default_kb_with_custom_config(self):
        """测试使用自定义配置创建默认知识库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_kb.db")
            
            # 初始化数据库
            db = initialize_database(db_path)
            
            # 自定义配置
            chunk_config = ChunkConfig(
                chunk_size=1024,
                chunk_overlap=100,
                parser_type="recursive"
            )
            
            retrieval_config = RetrievalConfig(
                retrieval_mode="vector",
                top_k=10,
                similarity_threshold=0.5
            )
            
            # 创建默认知识库
            default_kb = create_default_kb(
                db=db,
                embedding_model="custom-model",
                chunk_config=chunk_config,
                retrieval_config=retrieval_config
            )
            
            # 验证配置
            assert default_kb.chunk_config.chunk_size == 1024
            assert default_kb.chunk_config.chunk_overlap == 100
            assert default_kb.chunk_config.parser_type == "recursive"
            assert default_kb.retrieval_config.retrieval_mode == "vector"
            assert default_kb.retrieval_config.top_k == 10
            assert default_kb.retrieval_config.similarity_threshold == 0.5
    
    def test_create_default_kb_idempotent(self):
        """测试 create_default_kb 是幂等的"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_kb.db")
            
            # 初始化数据库
            db = initialize_database(db_path)
            
            # 第一次创建
            kb1 = create_default_kb(db, embedding_model="model1")
            
            # 第二次创建（应该返回已存在的）
            kb2 = create_default_kb(db, embedding_model="model2")
            
            # 验证返回的是同一个知识库
            assert kb1.id == kb2.id
            assert kb1.name == kb2.name
            # 注意：embedding_model 不会被更新
            assert kb2.embedding_model == "model1"
    
    def test_initialize_kb_system(self):
        """测试 initialize_kb_system 函数"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_kb.db")
            
            # 初始化系统
            db, default_kb = initialize_kb_system(
                db_path=db_path,
                create_default=True,
                embedding_model="system-model"
            )
            
            # 验证数据库
            assert isinstance(db, KnowledgeBaseDatabase)
            assert os.path.exists(db_path)
            
            # 验证默认知识库
            assert default_kb is not None
            assert default_kb.name == "default"
            assert default_kb.embedding_model == "system-model"
    
    def test_initialize_kb_system_without_default(self):
        """测试不创建默认知识库的初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_kb.db")
            
            # 初始化系统（不创建默认知识库）
            db, default_kb = initialize_kb_system(
                db_path=db_path,
                create_default=False
            )
            
            # 验证数据库
            assert isinstance(db, KnowledgeBaseDatabase)
            
            # 验证没有创建默认知识库
            assert default_kb is None
            
            # 验证数据库中没有知识库
            kbs, total = db.list_kbs()
            assert total == 0
    
    def test_get_or_create_default_kb(self):
        """测试 get_or_create_default_kb 函数"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_kb.db")
            
            # 初始化数据库（不创建默认知识库）
            db = initialize_database(db_path)
            
            # 第一次调用（应该创建）
            kb1 = get_or_create_default_kb(db)
            assert kb1 is not None
            assert kb1.name == "default"
            
            # 第二次调用（应该返回已存在的）
            kb2 = get_or_create_default_kb(db)
            assert kb2 is not None
            assert kb1.id == kb2.id
    
    def test_backward_compatibility(self):
        """测试向后兼容性"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_kb.db")
            
            # 模拟旧系统迁移到新系统
            db, default_kb = initialize_kb_system(
                db_path=db_path,
                create_default=True,
                embedding_model="bge-m3"
            )
            
            # 验证默认知识库使用了合理的默认值
            assert default_kb.chunk_config.chunk_size == 512
            assert default_kb.chunk_config.chunk_overlap == 50
            assert default_kb.retrieval_config.top_k == 5
            assert default_kb.retrieval_config.similarity_threshold == 0.3
            
            # 验证可以通过名称获取默认知识库
            kb_by_name = db.get_kb_by_name("default")
            assert kb_by_name is not None
            assert kb_by_name.id == default_kb.id


class TestMigrationScenarios:
    """测试迁移场景"""
    
    def test_fresh_installation(self):
        """测试全新安装场景"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_kb.db")
            
            # 全新安装
            db, default_kb = initialize_kb_system(
                db_path=db_path,
                create_default=True
            )
            
            # 验证系统状态
            assert os.path.exists(db_path)
            assert default_kb is not None
            
            kbs, total = db.list_kbs()
            assert total == 1
            assert kbs[0].name == "default"
    
    def test_existing_database_migration(self):
        """测试现有数据库迁移场景"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_kb.db")
            
            # 第一次初始化（模拟旧系统）
            db1 = initialize_database(db_path)
            
            # 第二次初始化（模拟迁移）
            db2 = initialize_database(db_path)
            
            # 验证数据库仍然可用
            kbs, total = db2.list_kbs()
            assert total == 0  # 没有知识库
            
            # 创建默认知识库
            default_kb = create_default_kb(db2)
            assert default_kb is not None
            
            # 验证知识库已创建
            kbs, total = db2.list_kbs()
            assert total == 1
    
    def test_multiple_initializations(self):
        """测试多次初始化的安全性"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_kb.db")
            
            # 多次初始化
            for i in range(3):
                db, default_kb = initialize_kb_system(
                    db_path=db_path,
                    create_default=True
                )
                
                # 验证只有一个默认知识库
                kbs, total = db.list_kbs()
                assert total == 1
                assert kbs[0].name == "default"


class TestErrorHandling:
    """测试错误处理"""
    
    def test_invalid_db_path(self):
        """测试无效的数据库路径"""
        # 使用不存在的目录（但会自动创建）
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "subdir", "test_kb.db")
            
            # 应该自动创建目录
            db = initialize_database(db_path)
            assert os.path.exists(db_path)
    
    def test_create_default_kb_with_invalid_config(self):
        """测试使用无效配置创建默认知识库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_kb.db")
            db = initialize_database(db_path)
            
            # 无效的分块配置
            with pytest.raises(ValueError):
                invalid_chunk_config = ChunkConfig(
                    chunk_size=50,  # 太小
                    chunk_overlap=100  # 大于 chunk_size
                )
                create_default_kb(
                    db=db,
                    chunk_config=invalid_chunk_config
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
