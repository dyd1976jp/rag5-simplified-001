"""
测试知识库提供者（缓存层）

验证 KnowledgeBaseProvider 类的缓存操作和线程安全性。
"""

import asyncio
import os
import tempfile
import uuid
from datetime import datetime

import pytest

from rag5.core.knowledge_base.database import KnowledgeBaseDatabase
from rag5.core.knowledge_base.provider import KnowledgeBaseProvider
from rag5.core.knowledge_base.models import (
    KnowledgeBase,
    ChunkConfig,
    RetrievalConfig
)


@pytest.fixture
def provider():
    """创建知识库提供者实例"""
    return KnowledgeBaseProvider()


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
def sample_kb2():
    """创建第二个示例知识库"""
    return KnowledgeBase(
        id=f"kb{uuid.uuid4().hex}",
        name="test_kb_2",
        description="Second test knowledge base",
        embedding_model="BAAI/bge-small-zh-v1.5",
        chunk_config=ChunkConfig(),
        retrieval_config=RetrievalConfig()
    )


class TestProviderBasicOperations:
    """测试提供者基本操作"""
    
    def test_add_kb(self, provider, sample_kb):
        """测试添加知识库到缓存"""
        provider.add(sample_kb)
        
        # 验证可以通过 ID 获取
        retrieved = provider.get(sample_kb.id)
        assert retrieved is not None
        assert retrieved.id == sample_kb.id
        assert retrieved.name == sample_kb.name
        
        # 验证可以通过名称获取
        retrieved_by_name = provider.get_by_name(sample_kb.name)
        assert retrieved_by_name is not None
        assert retrieved_by_name.id == sample_kb.id
    
    def test_get_nonexistent_kb(self, provider):
        """测试获取不存在的知识库"""
        result = provider.get("nonexistent_id")
        assert result is None
        
        result_by_name = provider.get_by_name("nonexistent_name")
        assert result_by_name is None
    
    def test_update_kb(self, provider, sample_kb):
        """测试更新知识库"""
        provider.add(sample_kb)
        
        # 更新知识库（保持名称不变）
        updated_kb = KnowledgeBase(
            id=sample_kb.id,
            name=sample_kb.name,
            description="Updated description",
            embedding_model=sample_kb.embedding_model,
            chunk_config=ChunkConfig(chunk_size=1024),
            retrieval_config=RetrievalConfig()
        )
        
        provider.update(updated_kb)
        
        # 验证更新
        retrieved = provider.get(sample_kb.id)
        assert retrieved.description == "Updated description"
        assert retrieved.chunk_config.chunk_size == 1024
    
    def test_update_kb_with_name_change(self, provider, sample_kb):
        """测试更新知识库名称"""
        provider.add(sample_kb)
        
        # 更新知识库名称
        updated_kb = KnowledgeBase(
            id=sample_kb.id,
            name="new_name",
            description=sample_kb.description,
            embedding_model=sample_kb.embedding_model,
            chunk_config=sample_kb.chunk_config,
            retrieval_config=sample_kb.retrieval_config
        )
        
        provider.update(updated_kb)
        
        # 验证旧名称不再有效
        assert provider.get_by_name(sample_kb.name) is None
        
        # 验证新名称有效
        retrieved = provider.get_by_name("new_name")
        assert retrieved is not None
        assert retrieved.id == sample_kb.id
    
    def test_delete_kb(self, provider, sample_kb):
        """测试删除知识库"""
        provider.add(sample_kb)
        
        # 验证存在
        assert provider.get(sample_kb.id) is not None
        
        # 删除
        provider.delete(sample_kb.id)
        
        # 验证已删除
        assert provider.get(sample_kb.id) is None
        assert provider.get_by_name(sample_kb.name) is None
    
    def test_delete_nonexistent_kb(self, provider):
        """测试删除不存在的知识库"""
        # 不应该抛出异常
        provider.delete("nonexistent_id")
    
    def test_exists(self, provider, sample_kb):
        """测试检查知识库是否存在"""
        assert not provider.exists(sample_kb.id)
        assert not provider.exists_by_name(sample_kb.name)
        
        provider.add(sample_kb)
        
        assert provider.exists(sample_kb.id)
        assert provider.exists_by_name(sample_kb.name)
    
    def test_list_all(self, provider, sample_kb, sample_kb2):
        """测试列出所有知识库"""
        assert len(provider.list_all()) == 0
        
        provider.add(sample_kb)
        assert len(provider.list_all()) == 1
        
        provider.add(sample_kb2)
        assert len(provider.list_all()) == 2
        
        kbs = provider.list_all()
        kb_ids = [kb.id for kb in kbs]
        assert sample_kb.id in kb_ids
        assert sample_kb2.id in kb_ids
    
    def test_clear(self, provider, sample_kb, sample_kb2):
        """测试清空缓存"""
        provider.add(sample_kb)
        provider.add(sample_kb2)
        
        assert len(provider) == 2
        
        provider.clear()
        
        assert len(provider) == 0
        assert provider.get(sample_kb.id) is None
        assert provider.get_by_name(sample_kb.name) is None
    
    def test_len(self, provider, sample_kb, sample_kb2):
        """测试 len() 操作"""
        assert len(provider) == 0
        
        provider.add(sample_kb)
        assert len(provider) == 1
        
        provider.add(sample_kb2)
        assert len(provider) == 2
        
        provider.delete(sample_kb.id)
        assert len(provider) == 1
    
    def test_contains(self, provider, sample_kb):
        """测试 'in' 操作符"""
        assert sample_kb.id not in provider
        
        provider.add(sample_kb)
        
        assert sample_kb.id in provider
    
    def test_get_statistics(self, provider, sample_kb, sample_kb2):
        """测试获取统计信息"""
        stats = provider.get_statistics()
        assert stats["total_kbs"] == 0
        assert stats["total_names"] == 0
        
        provider.add(sample_kb)
        provider.add(sample_kb2)
        
        stats = provider.get_statistics()
        assert stats["total_kbs"] == 2
        assert stats["total_names"] == 2


class TestProviderDatabaseIntegration:
    """测试提供者与数据库的集成"""
    
    @pytest.mark.anyio
    async def test_load_from_db(self, provider, temp_db):
        """测试从数据库加载知识库"""
        # 在数据库中创建知识库
        kb1 = KnowledgeBase(
            id=f"kb{uuid.uuid4().hex}",
            name="kb_1",
            description="KB 1",
            embedding_model="BAAI/bge-small-zh-v1.5"
        )
        kb2 = KnowledgeBase(
            id=f"kb{uuid.uuid4().hex}",
            name="kb_2",
            description="KB 2",
            embedding_model="BAAI/bge-small-zh-v1.5"
        )
        
        temp_db.create_kb(kb1)
        temp_db.create_kb(kb2)
        
        # 从数据库加载
        count = await provider.load_from_db(temp_db)
        
        assert count == 2
        assert len(provider) == 2
        assert provider.get(kb1.id) is not None
        assert provider.get(kb2.id) is not None
    
    @pytest.mark.anyio
    async def test_load_from_empty_db(self, provider, temp_db):
        """测试从空数据库加载"""
        count = await provider.load_from_db(temp_db)
        
        assert count == 0
        assert len(provider) == 0
    
    @pytest.mark.anyio
    async def test_refresh_kb(self, provider, temp_db, sample_kb):
        """测试刷新单个知识库"""
        # 在数据库中创建知识库
        temp_db.create_kb(sample_kb)
        
        # 加载到缓存
        await provider.load_from_db(temp_db)
        
        # 在数据库中更新
        temp_db.update_kb(sample_kb.id, description="Updated in DB")
        
        # 刷新缓存
        success = await provider.refresh_kb(temp_db, sample_kb.id)
        
        assert success is True
        
        # 验证缓存已更新
        cached_kb = provider.get(sample_kb.id)
        assert cached_kb.description == "Updated in DB"
    
    @pytest.mark.anyio
    async def test_refresh_nonexistent_kb(self, provider, temp_db, sample_kb):
        """测试刷新不存在的知识库"""
        # 添加到缓存但不在数据库中
        provider.add(sample_kb)
        
        # 尝试刷新
        success = await provider.refresh_kb(temp_db, sample_kb.id)
        
        assert success is False
        
        # 验证已从缓存中删除
        assert provider.get(sample_kb.id) is None


class TestProviderConcurrency:
    """测试提供者的并发安全性"""
    
    @pytest.mark.anyio
    async def test_concurrent_load_from_db(self, temp_db):
        """测试并发加载数据库"""
        # 创建多个知识库
        for i in range(10):
            kb = KnowledgeBase(
                id=f"kb{uuid.uuid4().hex}",
                name=f"kb_{i}",
                description=f"KB {i}",
                embedding_model="BAAI/bge-small-zh-v1.5"
            )
            temp_db.create_kb(kb)
        
        # 创建多个提供者实例并发加载
        providers = [KnowledgeBaseProvider() for _ in range(5)]
        
        tasks = [provider.load_from_db(temp_db) for provider in providers]
        results = await asyncio.gather(*tasks)
        
        # 验证所有提供者都加载了相同数量的知识库
        assert all(count == 10 for count in results)
        assert all(len(provider) == 10 for provider in providers)
    
    @pytest.mark.anyio
    async def test_concurrent_refresh(self, temp_db):
        """测试并发刷新"""
        # 创建知识库
        kb = KnowledgeBase(
            id=f"kb{uuid.uuid4().hex}",
            name="test_kb",
            description="Test KB",
            embedding_model="BAAI/bge-small-zh-v1.5"
        )
        temp_db.create_kb(kb)
        
        # 创建提供者并加载
        provider = KnowledgeBaseProvider()
        await provider.load_from_db(temp_db)
        
        # 并发刷新多次
        tasks = [provider.refresh_kb(temp_db, kb.id) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # 所有刷新都应该成功
        assert all(success for success in results)
        
        # 验证缓存仍然一致
        assert len(provider) == 1
        assert provider.get(kb.id) is not None


class TestProviderEdgeCases:
    """测试提供者的边界情况"""
    
    def test_multiple_add_same_kb(self, provider, sample_kb):
        """测试多次添加同一知识库"""
        provider.add(sample_kb)
        provider.add(sample_kb)  # 再次添加
        
        # 应该只有一个
        assert len(provider) == 1
    
    def test_update_before_add(self, provider, sample_kb):
        """测试在添加前更新"""
        # 直接更新（不存在的知识库）
        provider.update(sample_kb)
        
        # 应该被添加
        assert provider.get(sample_kb.id) is not None
    
    def test_name_collision_different_ids(self, provider, sample_kb):
        """测试不同 ID 但相同名称的知识库"""
        provider.add(sample_kb)
        
        # 创建不同 ID 但相同名称的知识库
        kb2 = KnowledgeBase(
            id=f"kb{uuid.uuid4().hex}",
            name=sample_kb.name,  # 相同名称
            description="Different KB",
            embedding_model="BAAI/bge-small-zh-v1.5"
        )
        
        provider.add(kb2)
        
        # 名称映射应该指向最后添加的
        retrieved = provider.get_by_name(sample_kb.name)
        assert retrieved.id == kb2.id
    
    def test_repr(self, provider, sample_kb):
        """测试字符串表示"""
        repr_str = repr(provider)
        assert "KnowledgeBaseProvider" in repr_str
        assert "kbs=0" in repr_str
        
        provider.add(sample_kb)
        
        repr_str = repr(provider)
        assert "kbs=1" in repr_str
