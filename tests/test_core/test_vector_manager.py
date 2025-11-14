"""
测试向量存储管理器

验证 VectorStoreManager 类的集合管理、数据插入和搜索功能。
"""

import uuid
from typing import List
from unittest.mock import Mock, MagicMock, patch, call

import pytest
from qdrant_client.models import (
    Distance,
    PointStruct,
    ScoredPoint,
    Filter,
    FieldCondition,
    MatchValue
)

from rag5.core.knowledge_base.vector_manager import VectorStoreManager


@pytest.fixture
def mock_qdrant_manager():
    """创建模拟的 QdrantManager"""
    manager = Mock()
    manager.ensure_collection = Mock()
    manager.delete_collection = Mock(return_value=True)
    manager.collection_exists = Mock(return_value=True)
    manager.upsert = Mock()
    manager.search = Mock(return_value=[])
    manager.get_collection_info = Mock(return_value={
        "vectors_count": 100,
        "points_count": 100,
        "status": "green"
    })
    manager.client = Mock()
    manager.client.delete = Mock()
    return manager


@pytest.fixture
def vector_manager(mock_qdrant_manager):
    """创建向量存储管理器实例"""
    return VectorStoreManager(mock_qdrant_manager)


@pytest.fixture
def sample_kb_id():
    """生成示例知识库 ID"""
    return f"kb{uuid.uuid4().hex}"


@pytest.fixture
def sample_chunks():
    """创建示例文档块"""
    return [
        {
            "id": "chunk_1",
            "text": "这是第一个文档块的内容",
            "file_id": "file_1",
            "source": "document.pdf",
            "chunk_index": 0
        },
        {
            "id": "chunk_2",
            "text": "这是第二个文档块的内容",
            "file_id": "file_1",
            "source": "document.pdf",
            "chunk_index": 1
        }
    ]


@pytest.fixture
def sample_embeddings():
    """创建示例向量嵌入"""
    return [
        [0.1] * 1024,  # 1024维向量
        [0.2] * 1024
    ]


class TestVectorManagerCollectionOperations:
    """测试集合操作"""
    
    @pytest.mark.anyio
    async def test_create_collection(self, vector_manager, mock_qdrant_manager, sample_kb_id):
        """测试创建集合"""
        await vector_manager.create_collection(sample_kb_id, embedding_dimension=1024)
        
        # 验证调用了 ensure_collection
        mock_qdrant_manager.ensure_collection.assert_called_once_with(
            collection_name=sample_kb_id,
            vector_dim=1024,
            distance=Distance.COSINE
        )
        
        # 验证缓存已更新
        assert vector_manager.collection_cache[sample_kb_id] is True
    
    @pytest.mark.anyio
    async def test_create_collection_with_custom_distance(
        self, vector_manager, mock_qdrant_manager, sample_kb_id
    ):
        """测试使用自定义距离度量创建集合"""
        await vector_manager.create_collection(
            sample_kb_id,
            embedding_dimension=768,
            distance=Distance.EUCLID
        )
        
        mock_qdrant_manager.ensure_collection.assert_called_once_with(
            collection_name=sample_kb_id,
            vector_dim=768,
            distance=Distance.EUCLID
        )
    
    @pytest.mark.anyio
    async def test_create_collection_failure(
        self, vector_manager, mock_qdrant_manager, sample_kb_id
    ):
        """测试集合创建失败"""
        mock_qdrant_manager.ensure_collection.side_effect = Exception("创建失败")
        
        with pytest.raises(Exception, match="创建失败"):
            await vector_manager.create_collection(sample_kb_id, embedding_dimension=1024)
    
    @pytest.mark.anyio
    async def test_delete_collection(self, vector_manager, mock_qdrant_manager, sample_kb_id):
        """测试删除集合"""
        # 先添加到缓存
        vector_manager.collection_cache[sample_kb_id] = True
        
        success = await vector_manager.delete_collection(sample_kb_id)
        
        assert success is True
        mock_qdrant_manager.delete_collection.assert_called_once_with(sample_kb_id)
        
        # 验证缓存已清除
        assert sample_kb_id not in vector_manager.collection_cache
    
    @pytest.mark.anyio
    async def test_delete_nonexistent_collection(
        self, vector_manager, mock_qdrant_manager, sample_kb_id
    ):
        """测试删除不存在的集合"""
        mock_qdrant_manager.collection_exists.return_value = False
        
        success = await vector_manager.delete_collection(sample_kb_id)
        
        # 应该返回成功（因为集合不存在）
        assert success is True
        # 不应该调用删除
        mock_qdrant_manager.delete_collection.assert_not_called()
    
    @pytest.mark.anyio
    async def test_delete_collection_failure(
        self, vector_manager, mock_qdrant_manager, sample_kb_id
    ):
        """测试删除集合失败"""
        mock_qdrant_manager.delete_collection.return_value = False
        
        success = await vector_manager.delete_collection(sample_kb_id)
        
        assert success is False
    
    @pytest.mark.anyio
    async def test_collection_exists_from_cache(
        self, vector_manager, mock_qdrant_manager, sample_kb_id
    ):
        """测试从缓存检查集合存在性"""
        # 设置缓存
        vector_manager.collection_cache[sample_kb_id] = True
        
        exists = await vector_manager.collection_exists(sample_kb_id)
        
        assert exists is True
        # 不应该调用实际查询
        mock_qdrant_manager.collection_exists.assert_not_called()
    
    @pytest.mark.anyio
    async def test_collection_exists_query(
        self, vector_manager, mock_qdrant_manager, sample_kb_id
    ):
        """测试查询集合存在性"""
        mock_qdrant_manager.collection_exists.return_value = True
        
        exists = await vector_manager.collection_exists(sample_kb_id)
        
        assert exists is True
        mock_qdrant_manager.collection_exists.assert_called_once_with(sample_kb_id)
        
        # 验证缓存已更新
        assert vector_manager.collection_cache[sample_kb_id] is True


class TestVectorManagerDataOperations:
    """测试数据操作"""
    
    @pytest.mark.anyio
    async def test_insert_chunks(
        self, vector_manager, mock_qdrant_manager, sample_kb_id, sample_chunks, sample_embeddings
    ):
        """测试插入文档块"""
        count = await vector_manager.insert_chunks(sample_kb_id, sample_chunks, sample_embeddings)
        
        assert count == 2
        
        # 验证调用了 upsert
        mock_qdrant_manager.upsert.assert_called_once()
        call_args = mock_qdrant_manager.upsert.call_args
        
        assert call_args[1]["collection_name"] == sample_kb_id
        points = call_args[1]["points"]
        assert len(points) == 2
        
        # 验证 point 结构
        assert points[0].id == "chunk_1"
        assert points[0].vector == sample_embeddings[0]
        assert points[0].payload["text"] == sample_chunks[0]["text"]
        assert points[0].payload["file_id"] == "file_1"
        assert points[0].payload["kb_id"] == sample_kb_id
    
    @pytest.mark.anyio
    async def test_insert_chunks_without_ids(
        self, vector_manager, mock_qdrant_manager, sample_kb_id, sample_embeddings
    ):
        """测试插入没有 ID 的文档块"""
        chunks_without_ids = [
            {"text": "内容1", "file_id": "f1"},
            {"text": "内容2", "file_id": "f1"}
        ]
        
        count = await vector_manager.insert_chunks(
            sample_kb_id, chunks_without_ids, sample_embeddings
        )
        
        assert count == 2
        
        # 验证自动生成了 ID
        call_args = mock_qdrant_manager.upsert.call_args
        points = call_args[1]["points"]
        
        assert points[0].id is not None
        assert points[1].id is not None
        assert points[0].id != points[1].id
    
    @pytest.mark.anyio
    async def test_insert_chunks_mismatch(
        self, vector_manager, sample_kb_id, sample_chunks
    ):
        """测试块数量与向量数量不匹配"""
        embeddings = [[0.1] * 1024]  # 只有一个向量
        
        with pytest.raises(ValueError, match="块数量.*与向量数量.*不匹配"):
            await vector_manager.insert_chunks(sample_kb_id, sample_chunks, embeddings)
    
    @pytest.mark.anyio
    async def test_insert_empty_chunks(self, vector_manager, sample_kb_id):
        """测试插入空列表"""
        count = await vector_manager.insert_chunks(sample_kb_id, [], [])
        
        assert count == 0
    
    @pytest.mark.anyio
    async def test_insert_chunks_collection_not_exists(
        self, vector_manager, mock_qdrant_manager, sample_kb_id, sample_chunks, sample_embeddings
    ):
        """测试向不存在的集合插入数据"""
        mock_qdrant_manager.collection_exists.return_value = False
        
        with pytest.raises(ValueError, match="向量集合不存在"):
            await vector_manager.insert_chunks(sample_kb_id, sample_chunks, sample_embeddings)
    
    @pytest.mark.anyio
    async def test_delete_by_file_id(
        self, vector_manager, mock_qdrant_manager, sample_kb_id
    ):
        """测试按文件 ID 删除"""
        file_id = "file_123"
        
        success = await vector_manager.delete_by_file_id(sample_kb_id, file_id)
        
        assert success is True
        
        # 验证调用了 delete
        mock_qdrant_manager.client.delete.assert_called_once()
        call_args = mock_qdrant_manager.client.delete.call_args
        
        assert call_args[1]["collection_name"] == sample_kb_id
        # 验证过滤器
        points_selector = call_args[1]["points_selector"]
        assert points_selector is not None
    
    @pytest.mark.anyio
    async def test_delete_by_file_id_collection_not_exists(
        self, vector_manager, mock_qdrant_manager, sample_kb_id
    ):
        """测试从不存在的集合删除"""
        mock_qdrant_manager.collection_exists.return_value = False
        
        success = await vector_manager.delete_by_file_id(sample_kb_id, "file_123")
        
        # 应该返回成功（集合不存在）
        assert success is True
        mock_qdrant_manager.client.delete.assert_not_called()


class TestVectorManagerSearchOperations:
    """测试搜索操作"""
    
    @pytest.mark.anyio
    async def test_search(self, vector_manager, mock_qdrant_manager, sample_kb_id):
        """测试搜索"""
        query_vector = [0.5] * 1024
        
        # 模拟搜索结果
        mock_results = [
            ScoredPoint(
                id="chunk_1",
                score=0.95,
                payload={"text": "结果1", "file_id": "f1"},
                version=1,
                vector=None
            ),
            ScoredPoint(
                id="chunk_2",
                score=0.85,
                payload={"text": "结果2", "file_id": "f1"},
                version=1,
                vector=None
            )
        ]
        mock_qdrant_manager.search.return_value = mock_results
        
        results = await vector_manager.search(sample_kb_id, query_vector, top_k=5)
        
        assert len(results) == 2
        assert results[0]["id"] == "chunk_1"
        assert results[0]["score"] == 0.95
        assert results[0]["payload"]["text"] == "结果1"
        
        # 验证调用参数
        mock_qdrant_manager.search.assert_called_once_with(
            collection_name=sample_kb_id,
            query_vector=query_vector,
            limit=5,
            score_threshold=None,
            query_filter=None
        )
    
    @pytest.mark.anyio
    async def test_search_with_threshold(
        self, vector_manager, mock_qdrant_manager, sample_kb_id
    ):
        """测试带阈值的搜索"""
        query_vector = [0.5] * 1024
        mock_qdrant_manager.search.return_value = []
        
        await vector_manager.search(
            sample_kb_id,
            query_vector,
            top_k=10,
            score_threshold=0.7
        )
        
        mock_qdrant_manager.search.assert_called_once()
        call_args = mock_qdrant_manager.search.call_args
        assert call_args[1]["score_threshold"] == 0.7
        assert call_args[1]["limit"] == 10
    
    @pytest.mark.anyio
    async def test_search_with_filter(
        self, vector_manager, mock_qdrant_manager, sample_kb_id
    ):
        """测试带过滤器的搜索"""
        query_vector = [0.5] * 1024
        query_filter = Filter(
            must=[FieldCondition(key="file_id", match=MatchValue(value="f1"))]
        )
        mock_qdrant_manager.search.return_value = []
        
        await vector_manager.search(
            sample_kb_id,
            query_vector,
            query_filter=query_filter
        )
        
        call_args = mock_qdrant_manager.search.call_args
        assert call_args[1]["query_filter"] == query_filter
    
    @pytest.mark.anyio
    async def test_search_collection_not_exists(
        self, vector_manager, mock_qdrant_manager, sample_kb_id
    ):
        """测试在不存在的集合中搜索"""
        mock_qdrant_manager.collection_exists.return_value = False
        query_vector = [0.5] * 1024
        
        with pytest.raises(ValueError, match="向量集合不存在"):
            await vector_manager.search(sample_kb_id, query_vector)
    
    @pytest.mark.anyio
    async def test_search_empty_results(
        self, vector_manager, mock_qdrant_manager, sample_kb_id
    ):
        """测试搜索无结果"""
        query_vector = [0.5] * 1024
        mock_qdrant_manager.search.return_value = []
        
        results = await vector_manager.search(sample_kb_id, query_vector)
        
        assert len(results) == 0


class TestVectorManagerUtilityMethods:
    """测试工具方法"""
    
    def test_get_collection_stats(self, vector_manager, mock_qdrant_manager, sample_kb_id):
        """测试获取集合统计信息"""
        stats = vector_manager.get_collection_stats(sample_kb_id)
        
        assert stats is not None
        assert stats["vectors_count"] == 100
        assert stats["points_count"] == 100
        assert stats["status"] == "green"
        
        mock_qdrant_manager.get_collection_info.assert_called_once_with(sample_kb_id)
    
    def test_get_collection_stats_failure(
        self, vector_manager, mock_qdrant_manager, sample_kb_id
    ):
        """测试获取统计信息失败"""
        mock_qdrant_manager.get_collection_info.side_effect = Exception("获取失败")
        
        stats = vector_manager.get_collection_stats(sample_kb_id)
        
        assert stats is None
    
    def test_clear_cache(self, vector_manager, sample_kb_id):
        """测试清除缓存"""
        # 添加一些缓存
        vector_manager.collection_cache[sample_kb_id] = True
        vector_manager.collection_cache["kb_2"] = False
        
        assert len(vector_manager.collection_cache) == 2
        
        vector_manager.clear_cache()
        
        assert len(vector_manager.collection_cache) == 0
    
    def test_repr(self, vector_manager, sample_kb_id):
        """测试字符串表示"""
        repr_str = repr(vector_manager)
        assert "VectorStoreManager" in repr_str
        assert "cached_collections=0" in repr_str
        
        vector_manager.collection_cache[sample_kb_id] = True
        
        repr_str = repr(vector_manager)
        assert "cached_collections=1" in repr_str


class TestVectorManagerEdgeCases:
    """测试边界情况"""
    
    @pytest.mark.anyio
    async def test_insert_chunks_with_extra_metadata(
        self, vector_manager, mock_qdrant_manager, sample_kb_id, sample_embeddings
    ):
        """测试插入包含额外元数据的块"""
        chunks = [
            {
                "id": "c1",
                "text": "内容",
                "file_id": "f1",
                "custom_field": "自定义值",
                "another_field": 123
            }
        ]
        
        await vector_manager.insert_chunks(sample_kb_id, chunks, [sample_embeddings[0]])
        
        call_args = mock_qdrant_manager.upsert.call_args
        points = call_args[1]["points"]
        
        # 验证额外字段被包含
        assert points[0].payload["custom_field"] == "自定义值"
        assert points[0].payload["another_field"] == 123
    
    @pytest.mark.anyio
    async def test_multiple_operations_cache_consistency(
        self, vector_manager, mock_qdrant_manager, sample_kb_id
    ):
        """测试多次操作后缓存一致性"""
        # 创建集合
        await vector_manager.create_collection(sample_kb_id, 1024)
        assert sample_kb_id in vector_manager.collection_cache
        
        # 检查存在性
        exists = await vector_manager.collection_exists(sample_kb_id)
        assert exists is True
        
        # 删除集合
        await vector_manager.delete_collection(sample_kb_id)
        assert sample_kb_id not in vector_manager.collection_cache
        
        # 再次检查存在性（应该查询实际状态）
        mock_qdrant_manager.collection_exists.return_value = False
        exists = await vector_manager.collection_exists(sample_kb_id)
        assert exists is False
