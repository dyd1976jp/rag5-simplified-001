"""
测试向量数据库工具模块
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from qdrant_client.models import ScoredPoint, PointStruct
from rag5.tools.vectordb import QdrantManager, ConnectionManager


def test_connection_manager_initialization():
    """测试ConnectionManager初始化"""
    manager = ConnectionManager()
    assert manager is not None


def test_connection_manager_connect():
    """测试连接Qdrant"""
    with patch('rag5.tools.vectordb.connection.QdrantClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        manager = ConnectionManager()
        client = manager.connect("http://localhost:6333")

        assert client is not None
        mock_client_class.assert_called_once_with(url="http://localhost:6333")


def test_connection_manager_test_connection_success():
    """测试连接测试（成功）"""
    with patch('rag5.tools.vectordb.connection.QdrantClient') as mock_client_class:
        mock_client = Mock()
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client_class.return_value = mock_client

        manager = ConnectionManager()
        manager.connect("http://localhost:6333")

        assert manager.test_connection() is True


def test_connection_manager_test_connection_failure():
    """测试连接测试（失败）"""
    with patch('rag5.tools.vectordb.connection.QdrantClient') as mock_client_class:
        mock_client = Mock()
        mock_client.get_collections.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client

        manager = ConnectionManager()
        manager.connect("http://localhost:6333")

        assert manager.test_connection() is False


def test_qdrant_manager_initialization():
    """测试QdrantManager初始化"""
    with patch('rag5.tools.vectordb.qdrant_client.QdrantClient'):
        manager = QdrantManager(url="http://localhost:6333")
        assert manager is not None


def test_ensure_collection_exists():
    """测试确保集合存在（已存在）"""
    with patch('rag5.tools.vectordb.qdrant_client.QdrantClient') as mock_client_class:
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.name = "test_collection"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection]
        mock_client.get_collections.return_value = mock_collections
        mock_client_class.return_value = mock_client

        manager = QdrantManager(url="http://localhost:6333")
        manager.ensure_collection("test_collection", vector_dim=1024)

        # 不应该调用create_collection
        mock_client.create_collection.assert_not_called()


def test_ensure_collection_create_new():
    """测试确保集合存在（创建新集合）"""
    with patch('rag5.tools.vectordb.qdrant_client.QdrantClient') as mock_client_class:
        mock_client = Mock()
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        mock_client_class.return_value = mock_client

        manager = QdrantManager(url="http://localhost:6333")
        manager.ensure_collection("new_collection", vector_dim=1024)

        # 应该调用create_collection
        mock_client.create_collection.assert_called_once()


def test_search_success():
    """测试搜索（成功）"""
    with patch('rag5.tools.vectordb.qdrant_client.QdrantClient') as mock_client_class:
        mock_client = Mock()

        # Mock搜索结果
        mock_points = [
            ScoredPoint(
                id="1",
                version=1,
                score=0.9,
                payload={"text": "测试内容", "source": "test.txt"},
                vector=None
            )
        ]
        mock_result = Mock()
        mock_result.points = mock_points
        mock_client.query_points.return_value = mock_result
        mock_client_class.return_value = mock_client

        manager = QdrantManager(url="http://localhost:6333")
        results = manager.search(
            collection="test_collection",
            vector=[0.1] * 1024,
            limit=5,
            threshold=0.7
        )

        assert len(results) == 1
        assert results[0].score == 0.9


def test_search_no_results():
    """测试搜索（无结果）"""
    with patch('rag5.tools.vectordb.qdrant_client.QdrantClient') as mock_client_class:
        mock_client = Mock()
        mock_result = Mock()
        mock_result.points = []
        mock_client.query_points.return_value = mock_result
        mock_client_class.return_value = mock_client

        manager = QdrantManager(url="http://localhost:6333")
        results = manager.search(
            collection="test_collection",
            vector=[0.1] * 1024,
            limit=5,
            threshold=0.7
        )

        assert len(results) == 0


def test_search_with_threshold_filtering():
    """测试搜索（阈值过滤）"""
    with patch('rag5.tools.vectordb.qdrant_client.QdrantClient') as mock_client_class:
        mock_client = Mock()

        # 创建不同分数的结果
        mock_points = [
            ScoredPoint(
                id="1", version=1, score=0.9,
                payload={"text": "高分内容"}, vector=None
            ),
            ScoredPoint(
                id="2", version=1, score=0.6,
                payload={"text": "低分内容"}, vector=None
            ),
        ]
        mock_result = Mock()
        mock_result.points = mock_points
        mock_client.query_points.return_value = mock_result
        mock_client_class.return_value = mock_client

        manager = QdrantManager(url="http://localhost:6333")
        results = manager.search(
            collection="test_collection",
            vector=[0.1] * 1024,
            limit=5,
            threshold=0.7
        )

        # 应该只返回分数>=0.7的结果
        assert len(results) == 1
        assert results[0].score == 0.9


def test_upsert_points():
    """测试上传点"""
    with patch('rag5.tools.vectordb.qdrant_client.QdrantClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        manager = QdrantManager(url="http://localhost:6333")

        points = [
            PointStruct(
                id="1",
                vector=[0.1] * 1024,
                payload={"text": "测试内容"}
            )
        ]

        manager.upsert(collection="test_collection", points=points)

        mock_client.upsert.assert_called_once()


def test_upsert_empty_points():
    """测试上传空点列表"""
    with patch('rag5.tools.vectordb.qdrant_client.QdrantClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        manager = QdrantManager(url="http://localhost:6333")
        manager.upsert(collection="test_collection", points=[])

        # 不应该调用upsert
        mock_client.upsert.assert_not_called()


def test_retry_with_backoff():
    """测试重试装饰器"""
    from rag5.tools.vectordb.retry import retry_with_backoff

    # 创建一个会失败然后成功的函数
    call_count = [0]

    @retry_with_backoff(max_retries=3, initial_delay=0.01)
    def flaky_function():
        call_count[0] += 1
        if call_count[0] < 2:
            raise Exception("Temporary error")
        return "success"

    result = flaky_function()

    assert result == "success"
    assert call_count[0] == 2


def test_retry_max_attempts_exceeded():
    """测试超过最大重试次数"""
    from rag5.tools.vectordb.retry import retry_with_backoff

    @retry_with_backoff(max_retries=2, initial_delay=0.01)
    def always_fails():
        raise Exception("Persistent error")

    with pytest.raises(Exception, match="Persistent error"):
        always_fails()


def test_connection_manager_reconnect():
    """测试重新连接"""
    with patch('rag5.tools.vectordb.connection.QdrantClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        manager = ConnectionManager()
        manager.connect("http://localhost:6333")

        # 重新连接
        if hasattr(manager, 'reconnect'):
            manager.reconnect()
            assert mock_client_class.call_count == 2


def test_qdrant_manager_get_collection_info():
    """测试获取集合信息"""
    with patch('rag5.tools.vectordb.qdrant_client.QdrantClient') as mock_client_class:
        mock_client = Mock()
        mock_info = Mock()
        mock_info.vectors_count = 100
        mock_client.get_collection.return_value = mock_info
        mock_client_class.return_value = mock_client

        manager = QdrantManager(url="http://localhost:6333")

        if hasattr(manager, 'get_collection_info'):
            info = manager.get_collection_info("test_collection")
            assert info.vectors_count == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
