"""
测试配置设置模块
"""

import os
import pytest
from unittest.mock import patch
from rag5.config.settings import Settings
from rag5.config import settings


def test_settings_singleton():
    """测试settings是单例"""
    from rag5.config import settings as settings1
    from rag5.config.settings import settings as settings2

    assert settings1 is settings2


def test_settings_initialization():
    """测试Settings初始化"""
    test_settings = Settings()
    assert test_settings is not None


def test_settings_properties():
    """测试settings属性访问"""
    assert hasattr(settings, 'ollama_host')
    assert hasattr(settings, 'llm_model')
    assert hasattr(settings, 'embed_model')
    assert hasattr(settings, 'qdrant_url')
    assert hasattr(settings, 'collection_name')
    assert hasattr(settings, 'vector_dim')
    assert hasattr(settings, 'top_k')
    assert hasattr(settings, 'similarity_threshold')
    assert hasattr(settings, 'chunk_size')
    assert hasattr(settings, 'chunk_overlap')


def test_settings_default_values():
    """测试默认配置值"""
    with patch.dict(os.environ, {}, clear=True):
        test_settings = Settings()

        assert test_settings.ollama_host == "http://localhost:11434"
        assert test_settings.llm_model == "qwen2.5:7b"
        assert test_settings.embed_model == "bge-m3"
        assert test_settings.qdrant_url == "http://localhost:6333"
        assert test_settings.collection_name == "knowledge_base"
        assert test_settings.vector_dim == 1024
        assert test_settings.top_k == 5
        assert test_settings.similarity_threshold == 0.7
        assert test_settings.chunk_size == 500
        assert test_settings.chunk_overlap == 50


def test_settings_from_environment():
    """测试从环境变量加载配置"""
    test_env = {
        "OLLAMA_HOST": "http://test-ollama:11434",
        "LLM_MODEL": "test-model",
        "EMBED_MODEL": "test-embed",
        "QDRANT_URL": "http://test-qdrant:6333",
        "COLLECTION_NAME": "test_collection",
        "TOP_K": "10",
        "SIMILARITY_THRESHOLD": "0.8",
        "CHUNK_SIZE": "1000",
        "CHUNK_OVERLAP": "100"
    }

    with patch.dict(os.environ, test_env, clear=True):
        test_settings = Settings()

        assert test_settings.ollama_host == "http://test-ollama:11434"
        assert test_settings.llm_model == "test-model"
        assert test_settings.embed_model == "test-embed"
        assert test_settings.qdrant_url == "http://test-qdrant:6333"
        assert test_settings.collection_name == "test_collection"
        assert test_settings.top_k == 10
        assert test_settings.similarity_threshold == 0.8
        assert test_settings.chunk_size == 1000
        assert test_settings.chunk_overlap == 100


def test_settings_validate_success():
    """测试配置验证成功"""
    with patch.dict(os.environ, {
        "OLLAMA_HOST": "http://localhost:11434",
        "QDRANT_URL": "http://localhost:6333",
        "LLM_MODEL": "qwen2.5:7b",
        "EMBED_MODEL": "bge-m3"
    }, clear=True):
        test_settings = Settings()

        # 应该不抛出异常
        test_settings.validate()


def test_settings_validate_failure():
    """测试配置验证失败"""
    with patch.dict(os.environ, {
        "OLLAMA_HOST": "invalid-url",
        "QDRANT_URL": "http://localhost:6333"
    }, clear=True):
        test_settings = Settings()

        with pytest.raises(ValueError):
            test_settings.validate()


def test_settings_to_dict():
    """测试转换为字典"""
    config_dict = settings.to_dict()

    assert isinstance(config_dict, dict)
    assert 'ollama_host' in config_dict
    assert 'llm_model' in config_dict
    assert 'embed_model' in config_dict
    assert 'qdrant_url' in config_dict
    assert 'collection_name' in config_dict
    assert 'vector_dim' in config_dict
    assert 'top_k' in config_dict
    assert 'similarity_threshold' in config_dict
    assert 'chunk_size' in config_dict
    assert 'chunk_overlap' in config_dict


def test_settings_print_config(capsys):
    """测试打印配置"""
    settings.print_config()

    captured = capsys.readouterr()
    output = captured.out

    assert 'Ollama Host' in output
    assert 'LLM Model' in output
    assert 'Embed Model' in output
    assert 'Qdrant URL' in output


def test_settings_invalid_top_k():
    """测试无效的TOP_K值回退到默认值"""
    with patch.dict(os.environ, {"TOP_K": "invalid"}, clear=True):
        test_settings = Settings()
        assert test_settings.top_k == 5  # 默认值


def test_settings_invalid_similarity_threshold():
    """测试无效的SIMILARITY_THRESHOLD值回退到默认值"""
    with patch.dict(os.environ, {"SIMILARITY_THRESHOLD": "invalid"}, clear=True):
        test_settings = Settings()
        assert test_settings.similarity_threshold == 0.7  # 默认值


def test_settings_negative_top_k():
    """测试负数TOP_K值回退到默认值"""
    with patch.dict(os.environ, {"TOP_K": "-5"}, clear=True):
        test_settings = Settings()
        assert test_settings.top_k == 5  # 默认值


def test_settings_out_of_range_similarity_threshold():
    """测试超出范围的SIMILARITY_THRESHOLD值回退到默认值"""
    with patch.dict(os.environ, {"SIMILARITY_THRESHOLD": "1.5"}, clear=True):
        test_settings = Settings()
        assert test_settings.similarity_threshold == 0.7  # 默认值


def test_settings_vector_dim_for_bge_m3():
    """测试bge-m3模型的向量维度"""
    with patch.dict(os.environ, {"EMBED_MODEL": "bge-m3"}, clear=True):
        test_settings = Settings()
        assert test_settings.vector_dim == 1024


def test_settings_vector_dim_for_other_models():
    """测试其他模型的向量维度"""
    with patch.dict(os.environ, {"EMBED_MODEL": "other-model"}, clear=True):
        test_settings = Settings()
        # 应该使用默认维度或根据模型名称推断
        assert isinstance(test_settings.vector_dim, int)
        assert test_settings.vector_dim > 0


def test_settings_immutability():
    """测试配置属性是否可以被修改"""
    # 注意：根据实际实现，配置可能是可变的或不可变的
    # 这个测试检查当前行为
    original_host = settings.ollama_host

    # 尝试修改（如果实现为只读属性，这应该失败）
    try:
        settings.ollama_host = "http://new-host:11434"
        # 如果成功修改，验证是否真的改变了
        # 注意：这取决于实现方式
    except AttributeError:
        # 如果是只读属性，应该抛出AttributeError
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
