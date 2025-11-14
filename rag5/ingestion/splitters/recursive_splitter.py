"""
递归字符分块器

使用递归方法将文档分割成更小的块，支持中英文。
"""

import logging
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class RecursiveSplitter:
    """
    递归字符分块器

    使用递归方法按照指定的分隔符将文档分割成更小的块。
    分隔符按优先级排序，优先使用段落分隔符，然后是句子分隔符，最后是字符级分隔。

    支持中英文文本的智能分块。

    Args:
        chunk_size: 每个块的最大字符数
        chunk_overlap: 相邻块之间的重叠字符数
        separators: 分隔符列表，按优先级排序。如果为None，使用默认的中英文分隔符

    示例:
        >>> splitter = RecursiveSplitter(chunk_size=500, chunk_overlap=50)
        >>> chunks = splitter.split_documents(documents)
        >>> print(f"分割成 {len(chunks)} 个块")
    """

    # 默认分隔符：优化用于中英文文本
    DEFAULT_SEPARATORS = [
        "\n\n",  # 双换行（段落分隔）
        "\n",    # 单换行（行分隔）
        "。",    # 中文句号
        "！",    # 中文感叹号
        "？",    # 中文问号
        ".",     # 英文句号
        "!",     # 英文感叹号
        "?",     # 英文问号
        " ",     # 空格（词边界）
        ""       # 字符级回退
    ]

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: List[str] = None
    ):
        """
        初始化递归分块器

        Args:
            chunk_size: 每个块的最大字符数
            chunk_overlap: 相邻块之间的重叠字符数
            separators: 分隔符列表。如果为None，使用默认分隔符
        """
        if chunk_size <= 0:
            raise ValueError(f"chunk_size必须大于0，当前值: {chunk_size}")

        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap不能为负数，当前值: {chunk_overlap}")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) 必须小于 chunk_size ({chunk_size})"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators if separators is not None else self.DEFAULT_SEPARATORS

        # 创建LangChain的RecursiveCharacterTextSplitter
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
            is_separator_regex=False
        )

        logger.debug(
            f"初始化RecursiveSplitter: chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}, separators={len(self.separators)}个"
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        将文档列表分割成更小的块

        Args:
            documents: 要分割的Document对象列表

        Returns:
            分割后的Document块列表

        Raises:
            ValueError: 如果documents为空或无效
        """
        if not documents:
            raise ValueError("文档列表不能为空")

        if not isinstance(documents, list):
            raise ValueError("documents必须是列表类型")

        logger.info(f"开始分割 {len(documents)} 个文档...")

        try:
            chunks = self._splitter.split_documents(documents)

            if not chunks:
                logger.warning("分割后未生成任何块")
                return []

            # 计算统计信息
            total_chars = sum(len(chunk.page_content) for chunk in chunks)
            avg_chunk_size = total_chars // len(chunks) if chunks else 0

            logger.info(f"✓ 分割完成: 生成 {len(chunks)} 个块")
            logger.info(f"  - 平均块大小: {avg_chunk_size} 字符")
            logger.info(f"  - 总字符数: {total_chars}")

            return chunks

        except Exception as e:
            logger.error(f"分割文档时出错: {e}")
            raise ValueError(f"分割文档失败: {e}")

    def split_text(self, text: str) -> List[str]:
        """
        将单个文本字符串分割成块

        Args:
            text: 要分割的文本

        Returns:
            分割后的文本块列表

        Raises:
            ValueError: 如果text为空或无效
        """
        if not text:
            raise ValueError("文本不能为空")

        if not isinstance(text, str):
            raise ValueError("text必须是字符串类型")

        try:
            chunks = self._splitter.split_text(text)
            logger.debug(f"将文本分割成 {len(chunks)} 个块")
            return chunks
        except Exception as e:
            logger.error(f"分割文本时出错: {e}")
            raise ValueError(f"分割文本失败: {e}")
