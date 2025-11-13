"""
数据摄取模块

处理文档加载、分块和向量化的完整流程。
"""

from .pipeline import IngestionPipeline, IngestionResult
from .loaders import BaseLoader, TextLoader, PDFLoader, MarkdownLoader
from .splitters import RecursiveSplitter
from .vectorizers import BatchVectorizer, VectorUploader, UploadResult


def ingest_directory(directory_path: str) -> IngestionResult:
    """
    便捷函数：摄取目录中的所有文档
    
    Args:
        directory_path: 文档目录路径
        
    Returns:
        IngestionResult: 摄取结果
    """
    pipeline = IngestionPipeline()
    return pipeline.ingest_directory(directory_path)


def ingest_file(file_path: str) -> IngestionResult:
    """
    便捷函数：摄取单个文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        IngestionResult: 摄取结果
    """
    pipeline = IngestionPipeline()
    return pipeline.ingest_file(file_path)


__all__ = [
    # 流程编排
    'IngestionPipeline',
    'IngestionResult',
    
    # 便捷函数
    'ingest_directory',
    'ingest_file',

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
