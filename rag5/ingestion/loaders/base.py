"""
文档加载器基类

定义所有文档加载器的通用接口。
"""

from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
from langchain_core.documents import Document


class BaseLoader(ABC):
    """
    文档加载器抽象基类

    所有具体的文档加载器都应该继承此类并实现 load() 和 supports() 方法。
    """

    @abstractmethod
    def load(self, file_path: str) -> List[Document]:
        """
        加载文档

        Args:
            file_path: 文件路径

        Returns:
            Document对象列表

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持或内容无效
            Exception: 其他加载错误
        """
        pass

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """
        检查是否支持该文件类型

        Args:
            file_path: 文件路径

        Returns:
            如果支持该文件类型返回True，否则返回False
        """
        pass

    def _validate_file(self, file_path: str, max_size: int = 100 * 1024 * 1024) -> None:
        """
        验证文件是否存在且大小合理

        Args:
            file_path: 文件路径
            max_size: 最大文件大小（字节），默认100MB

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件为空或超过大小限制
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if not path.is_file():
            raise ValueError(f"路径不是文件: {file_path}")

        file_size = path.stat().st_size

        if file_size == 0:
            raise ValueError(f"文件为空: {file_path}")

        if file_size > max_size:
            raise ValueError(
                f"文件超过大小限制 ({file_size / 1024 / 1024:.1f}MB > {max_size / 1024 / 1024:.1f}MB): {file_path}"
            )
