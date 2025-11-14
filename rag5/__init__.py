"""
RAG5 简化系统 - 主包

这是一个基于检索增强生成(RAG)技术的本地化问答系统。

主要功能：
- 配置管理：统一的配置加载和验证
- 核心代理：基于 LangChain 的 RAG 代理
- 工具系统：向量搜索、嵌入生成、向量数据库管理
- 数据摄取：文档加载、分块和向量化
- 接口：REST API 和 Web UI

使用示例：
    # 基本使用
    from rag5 import ask, settings

    # 配置系统
    print(f"LLM 模型: {settings.llm_model}")

    # 提问
    answer = ask("什么是 RAG?")
    print(answer)

    # 数据摄取
    from rag5 import ingest_directory
    result = ingest_directory("./docs")
    print(f"处理了 {result.documents_loaded} 个文档")
"""

__version__ = "2.0.0"

# ============================================================================
# 延迟导入优化
# ============================================================================
# 为了优化启动时间，我们使用延迟导入策略
# 只在实际使用时才导入重量级模块

def __getattr__(name):
    """延迟导入支持，优化启动性能"""
    # 配置模块 - 轻量级，立即导入
    if name == 'settings':
        from rag5.config import settings
        return settings
    elif name == 'config':  # 向后兼容
        from rag5.config import settings
        return settings

    # 核心代理模块 - 延迟导入
    elif name == 'SimpleRAGAgent':
        from rag5.core import SimpleRAGAgent
        return SimpleRAGAgent
    elif name == 'ask':
        from rag5.core import ask
        return ask
    elif name == 'AgentInitializer':
        from rag5.core import AgentInitializer
        return AgentInitializer
    elif name == 'MessageProcessor':
        from rag5.core import MessageProcessor
        return MessageProcessor
    elif name == 'ConversationHistory':
        from rag5.core import ConversationHistory
        return ConversationHistory
    elif name == 'ErrorHandler':
        from rag5.core import ErrorHandler
        return ErrorHandler
    elif name == 'RetryHandler':
        from rag5.core import RetryHandler
        return RetryHandler
    elif name == 'SYSTEM_PROMPT':
        from rag5.core import SYSTEM_PROMPT
        return SYSTEM_PROMPT
    elif name == 'SEARCH_TOOL_DESCRIPTION':
        from rag5.core import SEARCH_TOOL_DESCRIPTION
        return SEARCH_TOOL_DESCRIPTION

    # 工具模块 - 延迟导入
    elif name == 'tool_registry':
        from rag5.tools import tool_registry
        return tool_registry
    elif name == 'get_tools':
        from rag5.tools import get_tools
        return get_tools
    elif name == 'search_knowledge_base':
        from rag5.tools import search_knowledge_base
        return search_knowledge_base
    elif name == 'get_search_tool':
        from rag5.tools import get_search_tool
        return get_search_tool
    elif name == 'OllamaEmbeddingsManager':
        from rag5.tools import OllamaEmbeddingsManager
        return OllamaEmbeddingsManager
    elif name == 'QdrantManager':
        from rag5.tools import QdrantManager
        return QdrantManager
    elif name == 'ConnectionManager':
        from rag5.tools import ConnectionManager
        return ConnectionManager

    # 数据摄取模块 - 延迟导入
    elif name == 'IngestionPipeline':
        from rag5.ingestion import IngestionPipeline
        return IngestionPipeline
    elif name == 'IngestionResult':
        from rag5.ingestion import IngestionResult
        return IngestionResult
    elif name == 'BaseLoader':
        from rag5.ingestion import BaseLoader
        return BaseLoader
    elif name == 'TextLoader':
        from rag5.ingestion import TextLoader
        return TextLoader
    elif name == 'PDFLoader':
        from rag5.ingestion import PDFLoader
        return PDFLoader
    elif name == 'MarkdownLoader':
        from rag5.ingestion import MarkdownLoader
        return MarkdownLoader
    elif name == 'RecursiveSplitter':
        from rag5.ingestion import RecursiveSplitter
        return RecursiveSplitter
    elif name == 'BatchVectorizer':
        from rag5.ingestion import BatchVectorizer
        return BatchVectorizer
    elif name == 'VectorUploader':
        from rag5.ingestion import VectorUploader
        return VectorUploader
    elif name == 'UploadResult':
        from rag5.ingestion import UploadResult
        return UploadResult

    # 便捷函数 - 延迟导入
    elif name == 'ingest_directory':
        return ingest_directory
    elif name == 'ingest_file':
        return ingest_file
    elif name == 'ingest':  # 向后兼容
        return ingest_directory

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# ============================================================================
# 便捷函数
# ============================================================================

def ingest_directory(directory_path: str, **kwargs):
    """
    摄取目录中的所有文档

    这是一个便捷函数，用于快速摄取文档目录。

    参数:
        directory_path: 文档目录路径
        **kwargs: 传递给 IngestionPipeline 的额外参数

    返回:
        IngestionResult: 摄取结果，包含处理统计信息

    示例:
        >>> from rag5 import ingest_directory
        >>> result = ingest_directory("./docs")
        >>> print(f"成功处理 {result.documents_loaded} 个文档")
        >>> print(f"生成 {result.chunks_created} 个文本块")
        >>> print(f"上传 {result.vectors_uploaded} 个向量")
    """
    from rag5.ingestion import IngestionPipeline
    pipeline = IngestionPipeline()
    return pipeline.ingest_directory(directory_path, **kwargs)


def ingest_file(file_path: str, **kwargs):
    """
    摄取单个文档文件

    这是一个便捷函数，用于快速摄取单个文档。

    参数:
        file_path: 文档文件路径
        **kwargs: 传递给 IngestionPipeline 的额外参数

    返回:
        IngestionResult: 摄取结果，包含处理统计信息

    示例:
        >>> from rag5 import ingest_file
        >>> result = ingest_file("./docs/sample.pdf")
        >>> if result.success_rate == 1.0:
        ...     print("文档处理成功")
    """
    from rag5.ingestion import IngestionPipeline
    pipeline = IngestionPipeline()
    return pipeline.ingest_file(file_path, **kwargs)


# ============================================================================
# 向后兼容层
# ============================================================================
# 通过 __getattr__ 实现延迟导入，无需在此定义

# ============================================================================
# 公共接口导出
# ============================================================================

__all__ = [
    # 版本
    '__version__',

    # 配置
    'settings',
    'config',  # 向后兼容

    # 核心代理
    'SimpleRAGAgent',
    'ask',
    'AgentInitializer',
    'MessageProcessor',
    'ConversationHistory',
    'ErrorHandler',
    'RetryHandler',

    # 提示词
    'SYSTEM_PROMPT',
    'SEARCH_TOOL_DESCRIPTION',

    # 工具
    'tool_registry',
    'get_tools',
    'search_knowledge_base',
    'get_search_tool',
    'OllamaEmbeddingsManager',
    'QdrantManager',
    'ConnectionManager',

    # 数据摄取
    'IngestionPipeline',
    'IngestionResult',
    'ingest_directory',
    'ingest_file',
    'ingest',  # 向后兼容

    # 加载器
    'BaseLoader',
    'TextLoader',
    'PDFLoader',
    'MarkdownLoader',

    # 分块器
    'RecursiveSplitter',

    # 向量化
    'BatchVectorizer',
    'VectorUploader',
    'UploadResult',
]
