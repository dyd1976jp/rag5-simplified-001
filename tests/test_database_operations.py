"""
测试知识库数据库操作

验证 KnowledgeBaseDatabase 类的所有 CRUD 操作。
"""

import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

import pytest

from rag5.core.knowledge_base.database import KnowledgeBaseDatabase
from rag5.core.knowledge_base.models import (
    KnowledgeBase,
    FileEntity,
    FileStatus,
    ChunkConfig,
    RetrievalConfig
)


@pytest.fixture
def temp_db():
    """创建临时数据库用于测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_kb.db")
        db = KnowledgeBaseDatabase(db_path)
        yield db


@pytest.fixture
def sample_kb():
    """创建示例知识库"""
    return KnowledgeBase(
        id=f"kb{uuid.uuid4().hex}",
        name="test_kb",
        description="Test knowledge base",
        embedding_model="BAAI/bge-small-zh-v1.5",
        chunk_config=ChunkConfig(),
        retrieval_config=RetrievalConfig()
    )


@pytest.fixture
def sample_file(sample_kb):
    """创建示例文件"""
    return FileEntity(
        id=f"file{uuid.uuid4().hex}",
        kb_id=sample_kb.id,
        file_name="test.txt",
        file_path="/path/to/test.txt",
        file_extension=".txt",
        file_size=1024,
        file_md5="d41d8cd98f00b204e9800998ecf8427e",
        status=FileStatus.PENDING
    )


class TestKnowledgeBaseCRUD:
    """测试知识库 CRUD 操作"""
    
    def test_create_kb(self, temp_db, sample_kb):
        """测试创建知识库"""
        created_kb = temp_db.create_kb(sample_kb)
        
        assert created_kb.id == sample_kb.id
        assert created_kb.name == sample_kb.name
        assert created_kb.description == sample_kb.description
        assert created_kb.embedding_model == sample_kb.embedding_model
    
    def test_get_kb(self, temp_db, sample_kb):
        """测试获取知识库"""
        temp_db.create_kb(sample_kb)
        
        retrieved_kb = temp_db.get_kb(sample_kb.id)
        
        assert retrieved_kb is not None
        assert retrieved_kb.id == sample_kb.id
        assert retrieved_kb.name == sample_kb.name
    
    def test_get_kb_not_found(self, temp_db):
        """测试获取不存在的知识库"""
        result = temp_db.get_kb("nonexistent_id")
        assert result is None
    
    def test_get_kb_by_name(self, temp_db, sample_kb):
        """测试根据名称获取知识库"""
        temp_db.create_kb(sample_kb)
        
        retrieved_kb = temp_db.get_kb_by_name(sample_kb.name)
        
        assert retrieved_kb is not None
        assert retrieved_kb.name == sample_kb.name
    
    def test_list_kbs(self, temp_db):
        """测试列出知识库"""
        # 创建多个知识库
        for i in range(5):
            kb = KnowledgeBase(
                id=f"kb{uuid.uuid4().hex}",
                name=f"test_kb_{i}",
                description=f"Test KB {i}",
                embedding_model="BAAI/bge-small-zh-v1.5"
            )
            temp_db.create_kb(kb)
        
        # 测试分页
        kbs, total = temp_db.list_kbs(offset=0, limit=3)
        
        assert len(kbs) == 3
        assert total == 5
    
    def test_update_kb(self, temp_db, sample_kb):
        """测试更新知识库"""
        temp_db.create_kb(sample_kb)
        
        # 更新描述和配置
        updated_kb = temp_db.update_kb(
            sample_kb.id,
            description="Updated description",
            chunk_config=ChunkConfig(chunk_size=1024)
        )
        
        assert updated_kb is not None
        assert updated_kb.description == "Updated description"
        assert updated_kb.chunk_config.chunk_size == 1024
    
    def test_delete_kb(self, temp_db, sample_kb):
        """测试删除知识库"""
        temp_db.create_kb(sample_kb)
        
        # 删除知识库
        result = temp_db.delete_kb(sample_kb.id)
        assert result is True
        
        # 验证已删除
        retrieved_kb = temp_db.get_kb(sample_kb.id)
        assert retrieved_kb is None
    
    def test_get_kb_statistics(self, temp_db, sample_kb, sample_file):
        """测试获取知识库统计信息"""
        temp_db.create_kb(sample_kb)
        
        # 初始统计应该为 0
        stats = temp_db.get_kb_statistics(sample_kb.id)
        assert stats["document_count"] == 0
        assert stats["total_size"] == 0
        
        # 添加成功的文件
        sample_file.status = FileStatus.SUCCEEDED
        temp_db.create_file(sample_file)
        
        # 统计应该更新
        stats = temp_db.get_kb_statistics(sample_kb.id)
        assert stats["document_count"] == 1
        assert stats["total_size"] == 1024


class TestFileCRUD:
    """测试文件 CRUD 操作"""
    
    def test_create_file(self, temp_db, sample_kb, sample_file):
        """测试创建文件记录"""
        temp_db.create_kb(sample_kb)
        
        created_file = temp_db.create_file(sample_file)
        
        assert created_file.id == sample_file.id
        assert created_file.file_name == sample_file.file_name
        assert created_file.status == FileStatus.PENDING
    
    def test_get_file(self, temp_db, sample_kb, sample_file):
        """测试获取文件"""
        temp_db.create_kb(sample_kb)
        temp_db.create_file(sample_file)
        
        retrieved_file = temp_db.get_file(sample_file.id)
        
        assert retrieved_file is not None
        assert retrieved_file.id == sample_file.id
        assert retrieved_file.file_name == sample_file.file_name
    
    def test_list_files(self, temp_db, sample_kb):
        """测试列出文件"""
        temp_db.create_kb(sample_kb)
        
        # 创建多个文件
        for i in range(5):
            file = FileEntity(
                id=f"file{uuid.uuid4().hex}",
                kb_id=sample_kb.id,
                file_name=f"test_{i}.txt",
                file_path=f"/path/to/test_{i}.txt",
                file_extension=".txt",
                file_size=1024 * (i + 1),
                file_md5="d41d8cd98f00b204e9800998ecf8427e",
                status=FileStatus.SUCCEEDED if i % 2 == 0 else FileStatus.PENDING
            )
            temp_db.create_file(file)
        
        # 测试列出所有文件
        files, total = temp_db.list_files(sample_kb.id, offset=0, limit=10)
        assert len(files) == 5
        assert total == 5
        
        # 测试按状态过滤
        files, total = temp_db.list_files(
            sample_kb.id,
            status=FileStatus.SUCCEEDED,
            offset=0,
            limit=10
        )
        assert len(files) == 3
        assert total == 3
    
    def test_update_file_status(self, temp_db, sample_kb, sample_file):
        """测试更新文件状态"""
        temp_db.create_kb(sample_kb)
        temp_db.create_file(sample_file)
        
        # 更新状态为成功
        updated_file = temp_db.update_file_status(
            sample_file.id,
            FileStatus.SUCCEEDED,
            chunk_count=10
        )
        
        assert updated_file is not None
        assert updated_file.status == FileStatus.SUCCEEDED
        assert updated_file.chunk_count == 10
        
        # 更新状态为失败
        updated_file = temp_db.update_file_status(
            sample_file.id,
            FileStatus.FAILED,
            failed_reason="Test error"
        )
        
        assert updated_file.status == FileStatus.FAILED
        assert updated_file.failed_reason == "Test error"
    
    def test_delete_file(self, temp_db, sample_kb, sample_file):
        """测试删除文件"""
        temp_db.create_kb(sample_kb)
        temp_db.create_file(sample_file)
        
        # 删除文件
        result = temp_db.delete_file(sample_file.id)
        assert result is True
        
        # 验证已删除
        retrieved_file = temp_db.get_file(sample_file.id)
        assert retrieved_file is None


class TestTransactionAndErrorHandling:
    """测试事务和错误处理"""
    
    def test_duplicate_kb_name(self, temp_db, sample_kb):
        """测试重复的知识库名称"""
        temp_db.create_kb(sample_kb)
        
        # 尝试创建同名知识库
        duplicate_kb = KnowledgeBase(
            id=f"kb{uuid.uuid4().hex}",
            name=sample_kb.name,  # 相同名称
            description="Duplicate",
            embedding_model="BAAI/bge-small-zh-v1.5"
        )
        
        with pytest.raises(Exception):  # sqlite3.IntegrityError
            temp_db.create_kb(duplicate_kb)
    
    def test_cascade_delete(self, temp_db, sample_kb, sample_file):
        """测试级联删除"""
        temp_db.create_kb(sample_kb)
        temp_db.create_file(sample_file)
        
        # 删除知识库应该级联删除文件
        temp_db.delete_kb(sample_kb.id)
        
        # 验证文件也被删除
        retrieved_file = temp_db.get_file(sample_file.id)
        assert retrieved_file is None
    
    def test_duplicate_file_name_in_kb(self, temp_db, sample_kb, sample_file):
        """测试同一知识库中重复的文件名"""
        temp_db.create_kb(sample_kb)
        temp_db.create_file(sample_file)
        
        # 尝试创建同名文件
        duplicate_file = FileEntity(
            id=f"file{uuid.uuid4().hex}",
            kb_id=sample_kb.id,
            file_name=sample_file.file_name,  # 相同文件名
            file_path="/different/path.txt",
            file_extension=".txt",
            file_size=2048,
            file_md5="a1b2c3d4e5f6789012345678901234ab",  # Valid 32-char MD5
            status=FileStatus.PENDING
        )
        
        with pytest.raises(Exception):  # sqlite3.IntegrityError
            temp_db.create_file(duplicate_file)
