"""
批量向量化器

批量生成文档块的向量表示。
"""

import uuid
import logging
import time
from typing import List
from langchain_core.documents import Document
from qdrant_client.models import PointStruct

logger = logging.getLogger(__name__)


class BatchVectorizer:
    """
    批量向量化器

    将文档块批量转换为向量表示，并创建Qdrant Point对象。
    支持批量处理和错误重试。

    Args:
        embeddings: 嵌入模型实例（如OllamaEmbeddings）
        batch_size: 每批处理的文档数量
        max_retries: 单个文档的最大重试次数

    示例:
        >>> from langchain_ollama import OllamaEmbeddings
        >>> embeddings = OllamaEmbeddings(model="bge-m3")
        >>> vectorizer = BatchVectorizer(embeddings, batch_size=100)
        >>> points = vectorizer.vectorize(chunks)
        >>> print(f"生成了 {len(points)} 个向量")
    """

    def __init__(
        self,
        embeddings,
        batch_size: int = 100,
        max_retries: int = 2
    ):
        """
        初始化批量向量化器

        Args:
            embeddings: 嵌入模型实例
            batch_size: 每批处理的文档数量
            max_retries: 单个文档的最大重试次数
        """
        if batch_size <= 0:
            raise ValueError(f"batch_size必须大于0，当前值: {batch_size}")

        if max_retries < 0:
            raise ValueError(f"max_retries不能为负数，当前值: {max_retries}")

        self.embeddings = embeddings
        self.batch_size = batch_size
        self.max_retries = max_retries

        logger.debug(
            f"初始化BatchVectorizer: batch_size={batch_size}, "
            f"max_retries={max_retries}"
        )

    def vectorize(self, chunks: List[Document]) -> List[PointStruct]:
        """
        将文档块批量转换为向量

        Args:
            chunks: Document对象列表

        Returns:
            PointStruct对象列表，包含向量和元数据

        Raises:
            ValueError: 如果chunks为空或无效
        """
        if not chunks:
            raise ValueError("文档块列表不能为空")

        if not isinstance(chunks, list):
            raise ValueError("chunks必须是列表类型")

        logger.info(f"开始向量化 {len(chunks)} 个文档块...")

        points = []
        failed_indices = []

        for i, chunk in enumerate(chunks, 1):
            try:
                # 生成向量（带重试）
                vector = self._embed_with_retry(chunk.page_content, i)

                if vector is None:
                    logger.warning(f"块 {i}/{len(chunks)} 向量化失败，跳过")
                    failed_indices.append(i)
                    continue

                # 创建Point对象
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "text": chunk.page_content,
                        "source": chunk.metadata.get("source", "unknown"),
                        "metadata": chunk.metadata
                    }
                )

                points.append(point)

                # 定期输出进度
                if i % self.batch_size == 0 or i == len(chunks):
                    progress = (i / len(chunks)) * 100
                    logger.info(f"  进度: {i}/{len(chunks)} ({progress:.1f}%)")

            except Exception as e:
                logger.warning(f"处理块 {i}/{len(chunks)} 时出错: {e}")
                failed_indices.append(i)
                continue

        success_rate = (len(points) / len(chunks)) * 100 if chunks else 0

        logger.info(f"✓ 向量化完成:")
        logger.info(f"  - 成功: {len(points)}/{len(chunks)} ({success_rate:.1f}%)")
        if failed_indices:
            logger.warning(f"  - 失败: {len(failed_indices)} 个块")

        return points

    def _embed_with_retry(self, text: str, index: int) -> List[float]:
        """
        带重试的向量生成

        Args:
            text: 要向量化的文本
            index: 文档索引（用于日志）

        Returns:
            向量列表，失败返回None
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                vector = self.embeddings.embed_query(text)
                return vector

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    logger.debug(
                        f"块 {index} 向量化失败 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    time.sleep(1)  # 短暂延迟后重试
                else:
                    logger.warning(
                        f"块 {index} 向量化失败，已达最大重试次数: {e}"
                    )

        return None
