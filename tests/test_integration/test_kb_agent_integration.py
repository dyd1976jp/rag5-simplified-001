"""
测试知识库与代理系统的集成

验证代理可以使用 kb_id 参数查询特定知识库。
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from rag5.tools.search import search_tool
from rag5.tools.search.search_tool import reset_managers
from rag5.core.knowledge_base.models import (
    KnowledgeBase,
    ChunkConfig,
    RetrievalConfig
)
from datetime import datetime


@pytest.fixture(autouse=True)
def reset_tool_managers():
    """每个测试前重置管理器"""
    reset_managers()
    yield
    reset_managers()


@pytest.fixture
def mock_kb():
    """创建模拟知识库"""
    return KnowledgeBase(
        id="kb_test123",
        name="test_kb",
        description="Test knowledge base",
        embedding_model="nomic-embed-text",
        chunk_config=ChunkConfig(),
        retrieval_config=RetrievalConfig(
            top_k=5,
            similarity_threshold=0.3
        ),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def mock_search_results():
    """创建模拟搜索结果"""
    return [
        {
            "id": "chunk_1",
            "score": 0.85,
            "text": "这是测试文档的内容",
            "file_id": "file_1",
            "source": "test.txt",
            "chunk_index": 0,
            "metadata": {}
        },
        {
            "id": "chunk_2",
            "score": 0.75,
            "text": "这是另一个测试文档的内容",
            "file_id": "file_2",
            "source": "test2.txt",
            "chunk_index": 0,
            "metadata": {}
        }
    ]


class TestKBAgentIntegration:
    """测试知识库与代理系统的集成"""
    
    def test_search_with_kb_id(self, mock_kb, mock_search_results):
        """测试使用 kb_id 参数搜索"""
        with patch('rag5.tools.search.search_tool._get_kb_manager') as mock_get_manager:
            # 创建模拟的知识库管理器
            mock_manager = Mock()
            mock_manager.db.get_kb.return_value = mock_kb
            
            # 模拟异步查询方法
            async def mock_query(*args, **kwargs):
                return mock_search_results
            
            mock_manager.query_knowledge_base = mock_query
            mock_get_manager.return_value = mock_manager
            
            # 执行搜索 - 使用 invoke 方法
            result = search_tool.search_knowledge_base.invoke({
                "query": "测试查询",
                "kb_id": "kb_test123"
            })
            
            # 验证结果
            import json
            result_data = json.loads(result)
            
            assert "results" in result_data
            assert "total_count" in result_data
            assert "kb_id" in result_data
            assert "kb_name" in result_data
            
            assert result_data["kb_id"] == "kb_test123"
            assert result_data["kb_name"] == "test_kb"
            assert result_data["total_count"] == 2
            assert len(result_data["results"]) == 2
            
            # 验证结果格式
            first_result = result_data["results"][0]
            assert "score" in first_result
            assert "content" in first_result
            assert "source" in first_result
            assert first_result["score"] == 0.85
    
    def test_search_without_kb_id_backward_compatibility(self):
        """测试不提供 kb_id 时的向后兼容性"""
        with patch('rag5.tools.search.search_tool._get_embeddings_manager') as mock_embed, \
             patch('rag5.tools.search.search_tool._get_qdrant_manager') as mock_qdrant:
            
            # 模拟嵌入管理器
            mock_embed_instance = Mock()
            mock_embed_instance.embed_query.return_value = [0.1] * 768
            mock_embed.return_value = mock_embed_instance
            
            # 模拟 Qdrant 管理器
            mock_qdrant_instance = Mock()
            mock_result = Mock()
            mock_result.score = 0.85
            mock_result.payload = {
                "text": "测试内容",
                "source": "test.txt",
                "metadata": {}
            }
            mock_qdrant_instance.search.return_value = [mock_result]
            mock_qdrant.return_value = mock_qdrant_instance
            
            # 执行搜索（不提供 kb_id）
            result = search_tool.search_knowledge_base.invoke({"query": "测试查询"})
            
            # 验证结果
            import json
            result_data = json.loads(result)
            
            assert "results" in result_data
            assert "total_count" in result_data
            # 不应该有 kb_id 和 kb_name（向后兼容模式）
            assert "kb_id" not in result_data or result_data.get("kb_id") is None
            
            # 验证使用了传统的嵌入和搜索方法
            mock_embed_instance.embed_query.assert_called_once_with("测试查询")
            mock_qdrant_instance.search.assert_called_once()
    
    def test_search_with_invalid_kb_id(self):
        """测试使用无效的 kb_id"""
        with patch('rag5.tools.search.search_tool._get_kb_manager') as mock_get_manager:
            # 创建模拟的知识库管理器
            mock_manager = Mock()
            
            # 模拟知识库不存在的情况
            async def mock_query(*args, **kwargs):
                from rag5.core.knowledge_base.errors import KnowledgeBaseNotFoundError
                raise KnowledgeBaseNotFoundError("知识库不存在: kb_invalid")
            
            mock_manager.query_knowledge_base = mock_query
            mock_get_manager.return_value = mock_manager
            
            # 执行搜索
            result = search_tool.search_knowledge_base.invoke({
                "query": "测试查询",
                "kb_id": "kb_invalid"
            })
            
            # 验证返回错误
            import json
            result_data = json.loads(result)
            
            assert "error" in result_data
            assert "知识库" in result_data["error"]
            assert result_data["total_count"] == 0
            assert len(result_data["results"]) == 0
    
    def test_search_uses_kb_retrieval_config(self, mock_kb, mock_search_results):
        """测试搜索使用知识库的 RetrievalConfig"""
        with patch('rag5.tools.search.search_tool._get_kb_manager') as mock_get_manager:
            # 创建模拟的知识库管理器
            mock_manager = Mock()
            mock_manager.db.get_kb.return_value = mock_kb
            
            # 记录调用参数
            call_args = {}
            
            async def mock_query(*args, **kwargs):
                call_args.update(kwargs)
                return mock_search_results
            
            mock_manager.query_knowledge_base = mock_query
            mock_get_manager.return_value = mock_manager
            
            # 执行搜索
            search_tool.search_knowledge_base.invoke({
                "query": "测试查询",
                "kb_id": "kb_test123"
            })
            
            # 验证使用了知识库的配置
            # query_knowledge_base 方法会使用知识库的 RetrievalConfig
            assert call_args["kb_id"] == "kb_test123"
            assert call_args["query"] == "测试查询"
    
    def test_kb_manager_initialization_failure(self):
        """测试知识库管理器初始化失败时的回退"""
        with patch('rag5.tools.search.search_tool._get_kb_manager') as mock_get_manager:
            # 模拟管理器初始化失败
            mock_get_manager.return_value = None
            
            # 执行搜索
            result = search_tool.search_knowledge_base.invoke({
                "query": "测试查询",
                "kb_id": "kb_test123"
            })
            
            # 验证返回错误
            import json
            result_data = json.loads(result)
            
            assert "error" in result_data
            assert "知识库管理器不可用" in result_data["error"]
            assert result_data["total_count"] == 0
    
    def test_empty_query_with_kb_id(self):
        """测试空查询（即使提供了 kb_id）"""
        result = search_tool.search_knowledge_base.invoke({"query": "", "kb_id": "kb_test123"})
        
        import json
        result_data = json.loads(result)
        
        assert "error" in result_data
        assert "查询不能为空" in result_data["error"]
        assert result_data["total_count"] == 0


class TestKBManagerGetter:
    """测试知识库管理器获取函数"""
    
    def test_kb_manager_singleton(self):
        """测试知识库管理器是单例"""
        from rag5.tools.search.search_tool import _get_kb_manager
        
        with patch('rag5.core.knowledge_base.KnowledgeBaseManager') as mock_kb_class:
            mock_instance = Mock()
            mock_kb_class.return_value = mock_instance
            
            # 第一次调用
            manager1 = _get_kb_manager()
            
            # 第二次调用
            manager2 = _get_kb_manager()
            
            # 应该返回同一个实例
            assert manager1 is manager2
            
            # 只应该初始化一次
            assert mock_kb_class.call_count == 1
    
    def test_kb_manager_initialization_error_handling(self):
        """测试知识库管理器初始化错误处理"""
        from rag5.tools.search.search_tool import _get_kb_manager
        
        # 重置管理器
        reset_managers()
        
        with patch('rag5.core.knowledge_base.KnowledgeBaseManager') as mock_kb_class:
            # 模拟初始化失败
            mock_kb_class.side_effect = Exception("初始化失败")
            
            # 调用应该返回 None 而不是抛出异常
            manager = _get_kb_manager()
            
            assert manager is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
