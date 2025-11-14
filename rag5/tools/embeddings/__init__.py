"""
嵌入工具模块

提供文本向量化功能，支持 Ollama 嵌入模型。
"""

from rag5.tools.embeddings.ollama_embeddings import OllamaEmbeddingsManager

__all__ = [
    'OllamaEmbeddingsManager',
]
