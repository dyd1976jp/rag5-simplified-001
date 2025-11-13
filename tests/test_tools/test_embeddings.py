"""
测试嵌入工具模块
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from rag5.tools.embeddings import OllamaEmbeddingsManager


@pytest.fixture
def mock_ollama_api():
    """Mock Ollama API"""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post:

        # Mock list models response
        mock_list_response = Mock()
        mock_list_response.status_code = 200
        mock_list_response.json.return_value = {
            "models": [{"name": "bge-m3"}]
        }
        mock_get.return_value = mock_list_response

        # Mock embed response
        mock_embed_response = Mock()
        mock_embed_response.status_code = 200
        mock_embed_response.json.return_value = {
            "embedding": [0.1] * 1024
        }
        mock_post.return_value = mock_embed_response

        yield mock_get, mock_post


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


def test_embed_query_success(mock_ollama_api):
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

    with pytest.raises(ValueError, match="Text cannot be empty"):
        manager.embed_query("")


def test_embed_documents_success(mock_ollama_api):
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

    vectors = manager.embed_documents([])
    assert vectors == []


def test_embed_with_retry():
    """测试嵌入重试逻辑"""
    with patch('requests.post') as mock_post:
        # 第一次失败，第二次成功
        mock_post.side_effect = [
            Exception("Temporary error"),
            Mock(
                status_code=200,
                json=lambda: {"embedding": [0.1] * 1024}
            )
        ]

        manager = OllamaEmbeddingsManager(
            model="bge-m3",
            base_url="http://localhost:11434"
        )

        vector = manager.embed_query("测试")

        assert len(vector) == 1024
        assert mock_post.call_count == 2


def test_embed_max_retries_exceeded():
    """测试超过最大重试次数"""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("Persistent error")

        manager = OllamaEmbeddingsManager(
            model="bge-m3",
            base_url="http://localhost:11434"
        )

        with pytest.raises(Exception):
            manager.embed_query("测试")


def test_embed_with_custom_base_url():
    """测试使用自定义base_url"""
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embedding": [0.1] * 1024}
        mock_post.return_value = mock_response

        manager = OllamaEmbeddingsManager(
            model="bge-m3",
            base_url="http://custom-host:8080"
        )

        manager.embed_query("测试")

        # 验证使用了自定义URL
        call_args = mock_post.call_args
        assert "custom-host:8080" in call_args[0][0]


def test_embed_batch_processing():
    """测试批量处理"""
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embedding": [0.1] * 1024}
        mock_post.return_value = mock_response

        manager = OllamaEmbeddingsManager(
            model="bge-m3",
            base_url="http://localhost:11434"
        )

        # 嵌入大量文档
        texts = [f"文档{i}" for i in range(50)]
        vectors = manager.embed_documents(texts)

        assert len(vectors) == 50
        # 应该调用了50次（每个文档一次）
        assert mock_post.call_count == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
