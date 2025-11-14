"""
测试搜索工具模块
"""

import json
import pytest
from unittest.mock import Mock, patch
from qdrant_client.models import ScoredPoint
from rag5.tools.search import search_knowledge_base


def test_search_knowledge_base_empty_query():
    """测试空查询"""
    result = search_knowledge_base.invoke({"query": ""})
    result_dict = json.loads(result)

    assert "error" in result_dict
    assert "empty" in result_dict["error"].lower()
    assert result_dict["total_count"] == 0


def test_search_knowledge_base_with_results(mock_embeddings, mock_qdrant_client):
    """测试搜索返回结果"""
    # 创建mock搜索结果
    mock_point = ScoredPoint(
        id="test-id",
        version=1,
        score=0.85,
        payload={
            "text": "测试内容关于李小勇",
            "source": "test.pdf",
            "metadata": {"page": 1}
        },
        vector=None
    )

    mock_result = Mock()
    mock_result.points = [mock_point]
    mock_qdrant_client.query_points.return_value = mock_result

    with patch('rag5.tools.search.search_tool.OllamaEmbeddingsManager') as mock_embed_class, \
         patch('rag5.tools.search.search_tool.QdrantManager') as mock_qdrant_class:

        mock_embed_class.return_value = mock_embeddings
        mock_qdrant_class.return_value = mock_qdrant_client

        result = search_knowledge_base.invoke({"query": "李小勇合作入股"})
        result_dict = json.loads(result)

        assert "results" in result_dict
        assert result_dict["total_count"] == 1
        assert result_dict["results"][0]["score"] == 0.85
        assert result_dict["results"][0]["content"] == "测试内容关于李小勇"
        assert result_dict["results"][0]["source"] == "test.pdf"


def test_search_knowledge_base_no_results(mock_embeddings, mock_qdrant_client):
    """测试搜索无结果"""
    mock_result = Mock()
    mock_result.points = []
    mock_qdrant_client.query_points.return_value = mock_result

    with patch('rag5.tools.search.search_tool.OllamaEmbeddingsManager') as mock_embed_class, \
         patch('rag5.tools.search.search_tool.QdrantManager') as mock_qdrant_class:

        mock_embed_class.return_value = mock_embeddings
        mock_qdrant_class.return_value = mock_qdrant_client

        result = search_knowledge_base.invoke({"query": "不存在的查询"})
        result_dict = json.loads(result)

        assert "results" in result_dict
        assert result_dict["total_count"] == 0
        assert len(result_dict["results"]) == 0


def test_search_knowledge_base_connection_error(mock_embeddings):
    """测试连接错误处理"""
    with patch('rag5.tools.search.search_tool.OllamaEmbeddingsManager') as mock_embed_class, \
         patch('rag5.tools.search.search_tool.QdrantManager') as mock_qdrant_class:

        mock_embed_class.return_value = mock_embeddings
        mock_qdrant = Mock()
        mock_qdrant.search.side_effect = ConnectionError("连接失败")
        mock_qdrant_class.return_value = mock_qdrant

        result = search_knowledge_base.invoke({"query": "测试查询"})
        result_dict = json.loads(result)

        assert "error" in result_dict
        assert "connection" in result_dict["error"].lower() or "连接" in result_dict["error"]


def test_search_knowledge_base_embedding_error():
    """测试嵌入生成错误"""
    with patch('rag5.tools.search.search_tool.OllamaEmbeddingsManager') as mock_embed_class:
        mock_embeddings = Mock()
        mock_embeddings.embed_query.side_effect = Exception("嵌入生成失败")
        mock_embed_class.return_value = mock_embeddings

        result = search_knowledge_base.invoke({"query": "测试查询"})
        result_dict = json.loads(result)

        assert "error" in result_dict


def test_search_knowledge_base_result_formatting(mock_embeddings, mock_qdrant_client):
    """测试结果格式化"""
    # 创建多个mock结果
    mock_points = [
        ScoredPoint(
            id=f"id-{i}",
            version=1,
            score=0.9 - i * 0.1,
            payload={
                "text": f"内容 {i}",
                "source": f"doc{i}.pdf",
                "metadata": {"page": i}
            },
            vector=None
        )
        for i in range(3)
    ]

    mock_result = Mock()
    mock_result.points = mock_points
    mock_qdrant_client.query_points.return_value = mock_result

    with patch('rag5.tools.search.search_tool.OllamaEmbeddingsManager') as mock_embed_class, \
         patch('rag5.tools.search.search_tool.QdrantManager') as mock_qdrant_class:

        mock_embed_class.return_value = mock_embeddings
        mock_qdrant_class.return_value = mock_qdrant_client

        result = search_knowledge_base.invoke({"query": "测试"})
        result_dict = json.loads(result)

        assert result_dict["total_count"] == 3
        assert len(result_dict["results"]) == 3

        # 检查按分数排序
        for i, res in enumerate(result_dict["results"]):
            assert res["score"] == 0.9 - i * 0.1
            assert res["content"] == f"内容 {i}"
            assert res["source"] == f"doc{i}.pdf"


def test_search_knowledge_base_chinese_query(mock_embeddings, mock_qdrant_client):
    """测试中文查询"""
    mock_point = ScoredPoint(
        id="1",
        version=1,
        score=0.9,
        payload={"text": "这是中文内容", "source": "test.txt"},
        vector=None
    )

    mock_result = Mock()
    mock_result.points = [mock_point]
    mock_qdrant_client.query_points.return_value = mock_result

    with patch('rag5.tools.search.search_tool.OllamaEmbeddingsManager') as mock_embed_class, \
         patch('rag5.tools.search.search_tool.QdrantManager') as mock_qdrant_class:

        mock_embed_class.return_value = mock_embeddings
        mock_qdrant_class.return_value = mock_qdrant_client

        result = search_knowledge_base.invoke({"query": "中文查询测试"})
        result_dict = json.loads(result)

        assert result_dict["total_count"] == 1
        assert "中文" in result_dict["results"][0]["content"]


def test_search_knowledge_base_metadata_handling(mock_embeddings, mock_qdrant_client):
    """测试元数据处理"""
    mock_point = ScoredPoint(
        id="1",
        version=1,
        score=0.9,
        payload={
            "text": "测试内容",
            "source": "test.pdf",
            "metadata": {
                "page": 5,
                "chapter": "第一章",
                "author": "张三"
            }
        },
        vector=None
    )

    mock_result = Mock()
    mock_result.points = [mock_point]
    mock_qdrant_client.query_points.return_value = mock_result

    with patch('rag5.tools.search.search_tool.OllamaEmbeddingsManager') as mock_embed_class, \
         patch('rag5.tools.search.search_tool.QdrantManager') as mock_qdrant_class:

        mock_embed_class.return_value = mock_embeddings
        mock_qdrant_class.return_value = mock_qdrant_client

        result = search_knowledge_base.invoke({"query": "测试"})
        result_dict = json.loads(result)

        assert result_dict["results"][0]["metadata"]["page"] == 5
        assert result_dict["results"][0]["metadata"]["chapter"] == "第一章"
        assert result_dict["results"][0]["metadata"]["author"] == "张三"


def test_search_knowledge_base_tool_properties():
    """测试工具属性"""
    assert hasattr(search_knowledge_base, 'name')
    assert hasattr(search_knowledge_base, 'description')
    assert search_knowledge_base.name == "search_knowledge_base"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
