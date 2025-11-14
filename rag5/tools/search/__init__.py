"""
搜索工具模块

提供知识库向量搜索功能，包括：
- 基础向量搜索
- 自适应阈值搜索
- 混合搜索（向量+关键词）
- 查询扩展
"""

from rag5.tools.search.search_tool import (
    search_knowledge_base,
    get_search_tool,
    reset_managers
)
from rag5.tools.search.adaptive_search import AdaptiveSearchTool
from rag5.tools.search.hybrid_search import HybridSearchTool
from rag5.tools.search.query_expander import QueryExpander

__all__ = [
    'search_knowledge_base',
    'get_search_tool',
    'reset_managers',
    'AdaptiveSearchTool',
    'HybridSearchTool',
    'QueryExpander',
]
