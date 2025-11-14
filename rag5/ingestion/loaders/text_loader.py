"""
文本文件加载器

支持多种编码的文本文件加载。
"""

import logging
from typing import List
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader as LangChainTextLoader

from .base import BaseLoader

logger = logging.getLogger(__name__)


class TextLoader(BaseLoader):
    """
    文本文件加载器

    支持多种编码格式：UTF-8, GBK, GB2312, Latin-1
    自动尝试不同编码直到成功加载。

    示例:
        >>> loader = TextLoader()
        >>> docs = loader.load("document.txt")
        >>> print(f"加载了 {len(docs)} 个文档")
    """

    SUPPORTED_EXTENSIONS = {'.txt'}
    ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'latin-1']

    def supports(self, file_path: str) -> bool:
        """
        检查是否支持该文件类型

        Args:
            file_path: 文件路径

        Returns:
            如果文件扩展名为.txt返回True
        """
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def load(self, file_path: str) -> List[Document]:
        """
        加载文本文件

        尝试使用多种编码加载文件，直到成功或所有编码都失败。

        Args:
            file_path: 文件路径

        Returns:
            Document对象列表

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持、为空或无法解码
        """
        # 验证文件
        self._validate_file(file_path)

        if not self.supports(file_path):
            raise ValueError(f"不支持的文件类型: {file_path}")

        # 尝试不同编码
        last_error = None
        for encoding in self.ENCODINGS:
            try:
                logger.debug(f"尝试使用 {encoding} 编码加载 {file_path}")
                loader = LangChainTextLoader(str(file_path), encoding=encoding)
                docs = loader.load()

                # 验证加载的文档
                if not docs:
                    raise ValueError("未提取到内容")

                # 过滤空文档
                valid_docs = [doc for doc in docs if doc.page_content and doc.page_content.strip()]

                if not valid_docs:
                    raise ValueError("未提取到有效内容")

                logger.debug(f"成功使用 {encoding} 编码加载 {file_path}")
                return valid_docs

            except UnicodeDecodeError as e:
                last_error = e
                logger.debug(f"{encoding} 编码失败: {e}")
                continue
            except Exception as e:
                # 其他错误直接抛出
                raise ValueError(f"加载文件失败: {e}")

        # 所有编码都失败
        raise ValueError(
            f"无法使用支持的编码解码文件 ({', '.join(self.ENCODINGS)}): {file_path}"
        )
