"""
测试知识库API接口模块
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# 尝试导入TestClient
try:
    from starlette.testclient import TestClient
    TEST_CLIENT_AVAILABLE = True
except ImportError:
    TEST_CLIENT_AVAILABLE = False


@pytest.fixture
def mock_kb_manager():
    """Mock知识库管理器"""
    manager = Mock()
    
    # Mock async methods
    manager.create_knowledge_base = AsyncMock()
    manager.list_knowledge_bases = AsyncMock()
    manager.get_knowledge_base = AsyncMock()
    manager.update_knowledge_base = AsyncMock()
    manager.delete_knowledge_base = AsyncMock()
    manager.upload_file = AsyncMock()
    manager.list_files = AsyncMock()
    manager.delete_file = AsyncMock()
    manager.query_knowledge_base = AsyncMock()
    
    return manager


@pytest.fixture
def client(mock_kb_manager):
    """创建测试客户端"""
    if not TEST_CLIENT_AVAILABLE:
        pytest.skip("TestClient not available")

    from rag5.interfaces.api import create_app
    from rag5.interfaces.api.kb_routes import set_kb_manager
    
    # Set the mock manager
    set_kb_manager(mock_kb_manager)
    
    app = create_app()

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_kb():
    """示例知识库"""
    from rag5.core.knowledge_base import KnowledgeBase, ChunkConfig, RetrievalConfig
    
    return KnowledgeBase(
        id="kb_test123",
        name="test_kb",
        description="Test knowledge base",
        embedding_model="nomic-embed-text",
        chunk_config=ChunkConfig(),
        retrieval_config=RetrievalConfig(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        document_count=5,
        total_size=10000
    )


@pytest.fixture
def sample_file():
    """示例文件"""
    from rag5.core.knowledge_base import FileEntity, FileStatus
    
    return FileEntity(
        id="file_test123",
        kb_id="kb_test123",
        file_name="test.txt",
        file_path="/path/to/test.txt",
        file_extension=".txt",
        file_size=1000,
        file_md5="abc123def456789012345678901234ab",
        status=FileStatus.SUCCEEDED,
        chunk_count=10,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


def test_create_knowledge_base(client, mock_kb_manager, sample_kb):
    """测试创建知识库"""
    mock_kb_manager.create_knowledge_base.return_value = sample_kb
    
    response = client.post(
        "/api/v1/knowledge-bases",
        json={
            "name": "test_kb",
            "description": "Test knowledge base",
            "embedding_model": "nomic-embed-text"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_kb"
    assert data["id"] == "kb_test123"
    assert mock_kb_manager.create_knowledge_base.called


def test_list_knowledge_bases(client, mock_kb_manager, sample_kb):
    """测试列出知识库"""
    mock_kb_manager.list_knowledge_bases.return_value = ([sample_kb], 1)
    
    response = client.get("/api/v1/knowledge-bases?page=1&size=10")
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "test_kb"


def test_get_knowledge_base(client, mock_kb_manager, sample_kb):
    """测试获取知识库详情"""
    mock_kb_manager.get_knowledge_base.return_value = sample_kb
    
    response = client.get("/api/v1/knowledge-bases/kb_test123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "kb_test123"
    assert data["name"] == "test_kb"
    assert data["document_count"] == 5


def test_update_knowledge_base(client, mock_kb_manager, sample_kb):
    """测试更新知识库"""
    updated_kb = sample_kb.model_copy()
    updated_kb.description = "Updated description"
    mock_kb_manager.update_knowledge_base.return_value = updated_kb
    
    response = client.put(
        "/api/v1/knowledge-bases/kb_test123",
        json={"description": "Updated description"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"


def test_delete_knowledge_base(client, mock_kb_manager):
    """测试删除知识库"""
    mock_kb_manager.delete_knowledge_base.return_value = True
    
    response = client.delete("/api/v1/knowledge-bases/kb_test123")
    
    assert response.status_code == 204
    assert mock_kb_manager.delete_knowledge_base.called


def test_list_files(client, mock_kb_manager, sample_file):
    """测试列出文件"""
    mock_kb_manager.list_files.return_value = ([sample_file], 1)
    
    response = client.get("/api/v1/knowledge-bases/kb_test123/files")
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["file_name"] == "test.txt"


def test_delete_file(client, mock_kb_manager):
    """测试删除文件"""
    mock_kb_manager.delete_file.return_value = True
    
    response = client.delete("/api/v1/knowledge-bases/kb_test123/files/file_test123")
    
    assert response.status_code == 204
    assert mock_kb_manager.delete_file.called


def test_query_knowledge_base(client, mock_kb_manager):
    """测试查询知识库"""
    mock_results = [
        {
            "id": "chunk_1",
            "score": 0.95,
            "text": "Test content",
            "file_id": "file_test123",
            "source": "test.txt",
            "chunk_index": 0,
            "kb_id": "kb_test123",
            "metadata": {}
        }
    ]
    mock_kb_manager.query_knowledge_base.return_value = mock_results
    
    response = client.post(
        "/api/v1/knowledge-bases/kb_test123/query",
        json={"query": "test query"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["text"] == "Test content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
