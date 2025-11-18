"""
测试嵌入工具模块
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from rag5.tools.embeddings import OllamaEmbeddingsManager


@pytest.fixture
def mock_ollama_api():
    """Mock Ollama API"""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "bge-m3"}]
        }
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_embeddings():
    """Mock LangChain OllamaEmbeddings"""
    with patch('rag5.tools.embeddings.ollama_embeddings.OllamaEmbeddings') as mock_cls:
        mock_instance = MagicMock()

        def _embed_documents(texts):
            return [[0.1] * 1024 for _ in texts]

        mock_instance.embed_documents.side_effect = _embed_documents
        mock_instance.embed_query.side_effect = lambda text: [0.1] * 1024
        mock_cls.return_value = mock_instance
        yield mock_instance, mock_cls


def test_embeddings_manager_initialization():
    """测试OllamaEmbeddingsManager初始化"""
    manager = OllamaEmbeddingsManager(
        model="bge-m3",
        base_url="http://localhost:11434"
    )

    assert manager is not None
    assert manager.model == "bge-m3"
    assert manager.base_url == "http://localhost:11434"


def test_check_model_available_success(mock_ollama_api):
    """测试检查模型可用性（成功）"""
    manager = OllamaEmbeddingsManager(
        model="bge-m3",
        base_url="http://localhost:11434"
    )

    assert manager.check_model_available() is True


def test_check_model_available_not_found():
    """测试检查模型可用性（未找到）"""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "other-model"}]
        }
        mock_get.return_value = mock_response

        manager = OllamaEmbeddingsManager(
            model="bge-m3",
            base_url="http://localhost:11434"
        )

        assert manager.check_model_available() is False


def test_check_model_available_connection_error():
    """测试检查模型可用性（连接错误）"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Connection failed")

        manager = OllamaEmbeddingsManager(
            model="bge-m3",
            base_url="http://localhost:11434"
        )

        assert manager.check_model_available() is False


def test_embed_query_success(mock_ollama_api, mock_embeddings):
    """测试嵌入查询（成功）"""
    manager = OllamaEmbeddingsManager(
        model="bge-m3",
        base_url="http://localhost:11434"
    )

    vector = manager.embed_query("测试查询")

    assert isinstance(vector, list)
    assert len(vector) == 1024
    assert all(isinstance(v, float) for v in vector)


def test_embed_query_empty_text():
    """测试嵌入空文本"""
    manager = OllamaEmbeddingsManager(
        model="bge-m3",
        base_url="http://localhost:11434"
    )

    with pytest.raises(ValueError, match="查询文本不能为空"):
        manager.embed_query("")


def test_embed_documents_success(mock_ollama_api, mock_embeddings):
    """测试批量嵌入文档（成功）"""
    manager = OllamaEmbeddingsManager(
        model="bge-m3",
        base_url="http://localhost:11434"
    )

    texts = ["文档1", "文档2", "文档3"]
    vectors = manager.embed_documents(texts)

    assert isinstance(vectors, list)
    assert len(vectors) == 3
    assert all(len(v) == 1024 for v in vectors)


def test_embed_documents_empty_list():
    """测试嵌入空文档列表"""
    manager = OllamaEmbeddingsManager(
        model="bge-m3",
        base_url="http://localhost:11434"
    )

    with pytest.raises(ValueError, match="文档文本列表不能为空"):
        manager.embed_documents([])


def test_embed_documents_all_empty():
    """测试所有文档文本都为空"""
    manager = OllamaEmbeddingsManager(
        model="bge-m3",
        base_url="http://localhost:11434"
    )

    with pytest.raises(ValueError, match="所有文档文本都为空"):
        manager.embed_documents(["", "   "])


def test_embed_with_retry(mock_ollama_api, mock_embeddings):
    """测试嵌入重试逻辑"""
    manager = OllamaEmbeddingsManager(
        model="bge-m3",
        base_url="http://localhost:11434"
    )

    mock_instance, _ = mock_embeddings
    mock_instance.embed_query.side_effect = [
        Exception("Temporary error"),
        [0.1] * 1024
    ]

    with patch('rag5.tools.vectordb.retry.time.sleep'):
        vector = manager.embed_query("测试")

    assert len(vector) == 1024
    assert mock_instance.embed_query.call_count == 2


def test_embed_max_retries_exceeded(mock_ollama_api, mock_embeddings):
    """测试超过最大重试次数"""
    manager = OllamaEmbeddingsManager(
        model="bge-m3",
        base_url="http://localhost:11434"
    )

    mock_instance, _ = mock_embeddings
    mock_instance.embed_query.side_effect = Exception("Persistent error")

    with patch('rag5.tools.vectordb.retry.time.sleep'):
        with pytest.raises(Exception, match="Persistent error"):
            manager.embed_query("测试")


def test_embed_with_custom_base_url(mock_ollama_api, mock_embeddings):
    """测试使用自定义base_url"""
    manager = OllamaEmbeddingsManager(
        model="bge-m3",
        base_url="http://custom-host:8080"
    )

    manager.embed_query("测试")

    _, mock_cls = mock_embeddings
    mock_cls.assert_called_with(
        model="bge-m3",
        base_url="http://custom-host:8080"
    )


def test_embed_batch_processing(mock_ollama_api, mock_embeddings):
    """测试批量处理"""
    manager = OllamaEmbeddingsManager(
        model="bge-m3",
        base_url="http://localhost:11434",
        batch_size=10
    )

    mock_instance, _ = mock_embeddings

    texts = [f"文档{i}" for i in range(50)]
    vectors = manager.embed_documents(texts)

    assert len(vectors) == 50
    assert mock_instance.embed_documents.call_count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
