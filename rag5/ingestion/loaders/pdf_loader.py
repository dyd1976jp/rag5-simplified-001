"""
PDF文件加载器

支持PDF文档的加载和解析。
"""

import logging
from typing import List
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader

from .base import BaseLoader

logger = logging.getLogger(__name__)


class PDFLoader(BaseLoader):
    """
    PDF文件加载器

    使用PyPDF库加载和解析PDF文档。

    示例:
        >>> loader = PDFLoader()
        >>> docs = loader.load("document.pdf")
        >>> print(f"加载了 {len(docs)} 页")
    """

    SUPPORTED_EXTENSIONS = {'.pdf'}

    def supports(self, file_path: str) -> bool:
        """
        检查是否支持该文件类型

        Args:
            file_path: 文件路径

        Returns:
            如果文件扩展名为.pdf返回True
        """
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def load(self, file_path: str) -> List[Document]:
        """
        加载PDF文件

        Args:
            file_path: 文件路径

        Returns:
            Document对象列表，每页一个Document

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持、为空或解析失败
        """
        # 验证文件
        self._validate_file(file_path)

        if not self.supports(file_path):
            raise ValueError(f"不支持的文件类型: {file_path}")

        try:
            logger.debug(f"加载PDF文件: {file_path}")
            loader = PyPDFLoader(str(file_path))
            docs = loader.load()

            # 验证加载的文档
            if not docs:
                raise ValueError("未提取到内容")

            # 过滤空文档
            valid_docs = [doc for doc in docs if doc.page_content and doc.page_content.strip()]

            if not valid_docs:
                raise ValueError("未提取到有效内容")

            logger.debug(f"成功加载PDF文件，共 {len(valid_docs)} 页")
            return valid_docs

        except Exception as e:
            raise ValueError(f"加载PDF文件失败: {e}")
