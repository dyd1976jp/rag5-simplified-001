"""
工具模块

提供 RAG5 系统所需的各种工具功能，包括向量搜索、嵌入生成和向量数据库管理。
"""

# 工具注册
from rag5.tools.base import BaseTool
from rag5.tools.registry import tool_registry

# 嵌入工具
from rag5.tools.embeddings import OllamaEmbeddingsManager

# 向量数据库工具
from rag5.tools.vectordb import (
    ConnectionManager,
    QdrantManager,
    retry_with_backoff,
    execute_with_retry
)

# 搜索工具
from rag5.tools.search import (
    search_knowledge_base,
    get_search_tool,
    reset_managers
)

__all__ = [
    # 基础
    'BaseTool',
    'tool_registry',

    # 嵌入
    'OllamaEmbeddingsManager',

    # 向量数据库
    'ConnectionManager',
    'QdrantManager',
    'retry_with_backoff',
    'execute_with_retry',

    # 搜索
    'search_knowledge_base',
    'get_search_tool',
    'reset_managers',
]


def get_tools():
    """
    获取所有可用工具

    返回:
        工具列表

    示例:
        >>> from rag5.tools import get_tools
        >>> tools = get_tools()
        >>> print(f"可用工具: {[tool.name for tool in tools]}")
    """
    # 确保搜索工具已注册
    if not tool_registry.has_tool('search_knowledge_base'):
        tool_registry.register(search_knowledge_base)

    return tool_registry.get_all()
