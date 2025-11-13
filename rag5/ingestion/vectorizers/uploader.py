"""
向量上传器

将向量批量上传到Qdrant向量数据库。
"""

import logging
import time
from typing import List
from dataclasses import dataclass
from qdrant_client.models import PointStruct

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """
    上传结果数据类

    Attributes:
        total_points: 总点数
        uploaded_points: 成功上传的点数
        failed_batches: 失败的批次数
        success_rate: 成功率（百分比）
    """
    total_points: int
    uploaded_points: int
    failed_batches: int

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_points == 0:
            return 0.0
        return (self.uploaded_points / self.total_points) * 100


class VectorUploader:
    """
    向量上传器

    将向量批量上传到Qdrant向量数据库，支持批量处理和错误重试。

    Args:
        qdrant_manager: Qdrant管理器实例
        collection_name: 集合名称
        batch_size: 每批上传的点数
        max_retries: 批次上传的最大重试次数

    示例:
        >>> from rag5.tools.vectordb import QdrantManager
        >>> qdrant = QdrantManager("http://localhost:6333")
        >>> uploader = VectorUploader(qdrant, "my_collection")
        >>> result = uploader.upload_all(points)
        >>> print(f"上传成功率: {result.success_rate:.1f}%")
    """

    def __init__(
        self,
        qdrant_manager,
        collection_name: str,
        batch_size: int = 100,
        max_retries: int = 3
    ):
        """
        初始化向量上传器

        Args:
            qdrant_manager: Qdrant管理器实例
            collection_name: 集合名称
            batch_size: 每批上传的点数
            max_retries: 批次上传的最大重试次数
        """
        if not collection_name:
            raise ValueError("collection_name不能为空")

        if batch_size <= 0:
            raise ValueError(f"batch_size必须大于0，当前值: {batch_size}")

        if max_retries < 0:
            raise ValueError(f"max_retries不能为负数，当前值: {max_retries}")

        self.qdrant_manager = qdrant_manager
        self.collection_name = collection_name
        self.batch_size = batch_size
        self.max_retries = max_retries

        logger.debug(
            f"初始化VectorUploader: collection={collection_name}, "
            f"batch_size={batch_size}, max_retries={max_retries}"
        )

    def upload_batch(self, points: List[PointStruct]) -> int:
        """
        上传单个批次的点

        Args:
            points: PointStruct对象列表

        Returns:
            成功上传的点数

        Raises:
            Exception: 如果所有重试都失败
        """
        if not points:
            return 0

        last_error = None
        retry_delay = 1

        for attempt in range(self.max_retries + 1):
            try:
                self.qdrant_manager.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                return len(points)

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    logger.warning(
                        f"批次上传失败 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    logger.info(f"等待 {retry_delay}s 后重试...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 10)  # 指数退避，最大10秒
                else:
                    logger.error(f"批次上传失败，已达最大重试次数: {e}")

        raise last_error

    def upload_all(self, points: List[PointStruct]) -> UploadResult:
        """
        上传所有点，分批处理

        Args:
            points: PointStruct对象列表

        Returns:
            UploadResult对象，包含上传统计信息

        Raises:
            ValueError: 如果points为空或无效
        """
        if not points:
            raise ValueError("点列表不能为空")

        if not isinstance(points, list):
            raise ValueError("points必须是列表类型")

        logger.info(f"开始上传 {len(points)} 个向量到集合 '{self.collection_name}'...")
        logger.info(f"批次大小: {self.batch_size}")

        total_uploaded = 0
        failed_batches = 0

        # 分批上传
        num_batches = (len(points) + self.batch_size - 1) // self.batch_size

        for i in range(0, len(points), self.batch_size):
            batch = points[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1

            try:
                uploaded = self.upload_batch(batch)
                total_uploaded += uploaded

                progress = (total_uploaded / len(points)) * 100
                logger.info(
                    f"  ✓ 批次 {batch_num}/{num_batches}: "
                    f"上传 {uploaded} 个点 ({progress:.1f}%)"
                )

            except Exception as e:
                logger.error(f"  ✗ 批次 {batch_num}/{num_batches} 上传失败: {e}")
                failed_batches += 1
                continue

        # 创建结果
        result = UploadResult(
            total_points=len(points),
            uploaded_points=total_uploaded,
            failed_batches=failed_batches
        )

        logger.info(f"\n✓ 上传完成:")
        logger.info(f"  - 总点数: {result.total_points}")
        logger.info(f"  - 成功上传: {result.uploaded_points}")
        logger.info(f"  - 失败批次: {result.failed_batches}")
        logger.info(f"  - 成功率: {result.success_rate:.1f}%")

        return result
