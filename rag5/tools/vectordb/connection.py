"""
连接管理模块

管理 Qdrant 向量数据库的连接，提供连接测试和重连功能。
"""

import logging
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from rag5.tools.vectordb.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Qdrant 连接管理器

    管理与 Qdrant 向量数据库的连接，提供连接测试、重连等功能。

    属性:
        url: Qdrant 服务地址
        client: Qdrant 客户端实例

    示例:
        >>> from rag5.tools.vectordb import ConnectionManager
        >>>
        >>> manager = ConnectionManager("http://localhost:6333")
        >>> if manager.test_connection():
        ...     print("连接成功")
        >>> client = manager.get_client()
    """

    def __init__(self, url: str):
        """
        初始化连接管理器

        参数:
            url: Qdrant 服务地址
        """
        self.url = url
        self._client: Optional[QdrantClient] = None
        logger.debug(f"初始化连接管理器: {url}")

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def connect(self) -> QdrantClient:
        """
        连接到 Qdrant

        返回:
            Qdrant 客户端实例

        异常:
            ConnectionError: 连接失败

        示例:
            >>> manager = ConnectionManager("http://localhost:6333")
            >>> client = manager.connect()
        """
        try:
            logger.info(f"正在连接到 Qdrant: {self.url}")
            self._client = QdrantClient(url=self.url)

            # 测试连接
            self._client.get_collections()

            logger.info(f"✓ 成功连接到 Qdrant: {self.url}")
            return self._client
        except Exception as e:
            logger.error(f"连接 Qdrant 失败: {e}")
            raise ConnectionError(f"无法连接到 Qdrant ({self.url}): {e}")

    def test_connection(self) -> bool:
        """
        测试连接是否正常

        返回:
            连接是否正常

        示例:
            >>> manager = ConnectionManager("http://localhost:6333")
            >>> if manager.test_connection():
            ...     print("连接正常")
        """
        try:
            if self._client is None:
                self.connect()

            # 尝试获取集合列表来测试连接
            self._client.get_collections()
            logger.debug("Qdrant 连接测试成功")
            return True
        except Exception as e:
            logger.warning(f"Qdrant 连接测试失败: {e}")
            return False

    def reconnect(self) -> QdrantClient:
        """
        重新连接到 Qdrant

        返回:
            Qdrant 客户端实例

        异常:
            ConnectionError: 重连失败

        示例:
            >>> manager = ConnectionManager("http://localhost:6333")
            >>> client = manager.reconnect()
        """
        logger.info("正在重新连接到 Qdrant...")
        self._client = None
        return self.connect()

    def get_client(self) -> QdrantClient:
        """
        获取 Qdrant 客户端

        如果客户端未初始化，将自动连接。

        返回:
            Qdrant 客户端实例

        异常:
            ConnectionError: 连接失败

        示例:
            >>> manager = ConnectionManager("http://localhost:6333")
            >>> client = manager.get_client()
            >>> collections = client.get_collections()
        """
        if self._client is None:
            self.connect()
        return self._client

    def close(self) -> None:
        """
        关闭连接

        示例:
            >>> manager = ConnectionManager("http://localhost:6333")
            >>> manager.close()
        """
        if self._client is not None:
            logger.info("关闭 Qdrant 连接")
            self._client = None

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def __repr__(self) -> str:
        """返回连接管理器的字符串表示"""
        status = "connected" if self._client else "disconnected"
        return f"<ConnectionManager(url='{self.url}', status='{status}')>"
