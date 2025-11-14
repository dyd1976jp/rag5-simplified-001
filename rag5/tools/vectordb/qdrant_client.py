"""
Qdrant 客户端封装模块

封装 Qdrant 客户端操作，提供集合管理、搜索和上传等功能。
"""

import logging
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    ScoredPoint,
    Filter,
    FieldCondition,
    MatchValue
)
from qdrant_client.http.exceptions import UnexpectedResponse

from rag5.tools.vectordb.connection import ConnectionManager
from rag5.tools.vectordb.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class QdrantManager:
    """
    Qdrant 管理器

    封装 Qdrant 客户端操作，提供集合管理、向量搜索和数据上传等功能。

    属性:
        url: Qdrant 服务地址
        connection_manager: 连接管理器

    示例:
        >>> from rag5.tools.vectordb import QdrantManager
        >>>
        >>> manager = QdrantManager("http://localhost:6333")
        >>> manager.ensure_collection("my_collection", vector_dim=1024)
        >>> results = manager.search("my_collection", query_vector, limit=5)
    """

    def __init__(self, url: str):
        """
        初始化 Qdrant 管理器

        参数:
            url: Qdrant 服务地址
        """
        self.url = url
        self.connection_manager = ConnectionManager(url)
        logger.debug(f"初始化 Qdrant 管理器: {url}")

    @property
    def client(self) -> QdrantClient:
        """获取 Qdrant 客户端"""
        return self.connection_manager.get_client()

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def ensure_collection(
        self,
        collection_name: str,
        vector_dim: int,
        distance: Distance = Distance.COSINE
    ) -> None:
        """
        确保集合存在

        如果集合不存在，则创建它。

        参数:
            collection_name: 集合名称
            vector_dim: 向量维度
            distance: 距离度量方式（默认为余弦距离）

        示例:
            >>> manager = QdrantManager("http://localhost:6333")
            >>> manager.ensure_collection("knowledge_base", vector_dim=1024)
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if collection_name not in collection_names:
                logger.info(f"创建集合 '{collection_name}'...")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_dim,
                        distance=distance
                    )
                )
                logger.info(f"✓ 集合 '{collection_name}' 创建成功")
            else:
                logger.debug(f"集合 '{collection_name}' 已存在")
        except Exception as e:
            logger.error(f"确保集合存在时出错: {e}")
            raise

    def collection_exists(self, collection_name: str) -> bool:
        """
        检查集合是否存在

        参数:
            collection_name: 集合名称

        返回:
            集合是否存在

        示例:
            >>> manager = QdrantManager("http://localhost:6333")
            >>> if manager.collection_exists("knowledge_base"):
            ...     print("集合存在")
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            return collection_name in collection_names
        except Exception as e:
            logger.error(f"检查集合是否存在时出错: {e}")
            return False

    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """
        获取集合信息

        参数:
            collection_name: 集合名称

        返回:
            集合信息字典，如果集合不存在则返回 None

        示例:
            >>> manager = QdrantManager("http://localhost:6333")
            >>> info = manager.get_collection_info("knowledge_base")
            >>> print(f"向量数量: {info['vectors_count']}")
        """
        try:
            collection = self.client.get_collection(collection_name)
            return {
                'vectors_count': collection.vectors_count,
                'points_count': collection.points_count,
                'status': collection.status,
            }
        except Exception as e:
            logger.error(f"获取集合信息时出错: {e}")
            return None

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        query_filter: Optional[Filter] = None
    ) -> List[ScoredPoint]:
        """
        向量搜索

        参数:
            collection_name: 集合名称
            query_vector: 查询向量
            limit: 返回结果数量
            score_threshold: 相似度阈值（可选）
            query_filter: 查询过滤器（可选）

        返回:
            搜索结果列表

        示例:
            >>> manager = QdrantManager("http://localhost:6333")
            >>> results = manager.search(
            ...     "knowledge_base",
            ...     query_vector=[0.1, 0.2, ...],
            ...     limit=5,
            ...     score_threshold=0.7
            ... )
            >>> for result in results:
            ...     print(f"Score: {result.score}, Text: {result.payload['text']}")
        """
        try:
            import time
            start_time = time.time()
            
            logger.debug(f"搜索集合 '{collection_name}'")
            logger.debug(f"搜索参数 - limit: {limit}, threshold: {score_threshold}")
            logger.debug(f"查询向量维度: {len(query_vector)}")
            if query_filter:
                logger.debug(f"使用过滤器: {query_filter}")

            results = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            ).points
            
            search_time = time.time() - start_time

            logger.info(f"找到 {len(results)} 个结果 (耗时: {search_time:.3f}秒)")
            
            # 记录结果统计
            if results:
                scores = [result.score for result in results]
                logger.debug(
                    f"相似度分数范围: {min(scores):.4f} - {max(scores):.4f}, "
                    f"平均: {sum(scores)/len(scores):.4f}"
                )
                
                # 记录前几个结果的来源
                sources = [result.payload.get('source', 'unknown') for result in results[:3]]
                logger.debug(f"前3个结果来源: {sources}")
            else:
                logger.warning(
                    f"未找到结果. 当前阈值: {score_threshold}. "
                    f"建议降低阈值或检查数据是否已索引"
                )
            
            return results
        except Exception as e:
            logger.error(f"搜索时出错: {e}", exc_info=True)
            raise

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def upsert(
        self,
        collection_name: str,
        points: List[PointStruct]
    ) -> None:
        """
        上传或更新向量点

        参数:
            collection_name: 集合名称
            points: 向量点列表

        示例:
            >>> from qdrant_client.models import PointStruct
            >>>
            >>> manager = QdrantManager("http://localhost:6333")
            >>> points = [
            ...     PointStruct(
            ...         id=1,
            ...         vector=[0.1, 0.2, ...],
            ...         payload={"text": "文本内容", "source": "文档.pdf"}
            ...     )
            ... ]
            >>> manager.upsert("knowledge_base", points)
        """
        try:
            import time
            start_time = time.time()
            
            logger.debug(f"上传 {len(points)} 个点到集合 '{collection_name}'")
            
            # 记录向量信息
            if points:
                vector_dim = len(points[0].vector)
                logger.debug(f"向量维度: {vector_dim}")
                
                # 统计来源
                sources = set()
                for point in points[:10]:  # 只检查前10个
                    if 'source' in point.payload:
                        sources.add(point.payload['source'])
                if sources:
                    logger.debug(f"数据来源: {list(sources)[:5]}")

            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            upload_time = time.time() - start_time

            logger.info(f"✓ 成功上传 {len(points)} 个点 (耗时: {upload_time:.3f}秒)")
            logger.debug(f"上传速度: {len(points)/upload_time:.1f} 点/秒")
        except Exception as e:
            logger.error(f"上传向量点时出错: {e}", exc_info=True)
            raise

    def delete_collection(self, collection_name: str) -> bool:
        """
        删除集合

        参数:
            collection_name: 集合名称

        返回:
            是否成功删除

        示例:
            >>> manager = QdrantManager("http://localhost:6333")
            >>> manager.delete_collection("old_collection")
        """
        try:
            logger.info(f"删除集合 '{collection_name}'...")
            self.client.delete_collection(collection_name)
            logger.info(f"✓ 集合 '{collection_name}' 已删除")
            return True
        except Exception as e:
            logger.error(f"删除集合时出错: {e}")
            return False

    def count_points(self, collection_name: str) -> int:
        """
        统计集合中的点数量

        参数:
            collection_name: 集合名称

        返回:
            点的数量

        示例:
            >>> manager = QdrantManager("http://localhost:6333")
            >>> count = manager.count_points("knowledge_base")
            >>> print(f"集合中有 {count} 个向量")
        """
        try:
            collection = self.client.get_collection(collection_name)
            return collection.points_count
        except Exception as e:
            logger.error(f"统计点数量时出错: {e}")
            return 0

    def test_connection(self) -> bool:
        """
        测试连接

        返回:
            连接是否正常

        示例:
            >>> manager = QdrantManager("http://localhost:6333")
            >>> if manager.test_connection():
            ...     print("连接正常")
        """
        return self.connection_manager.test_connection()

    def close(self) -> None:
        """
        关闭连接

        示例:
            >>> manager = QdrantManager("http://localhost:6333")
            >>> manager.close()
        """
        self.connection_manager.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def __repr__(self) -> str:
        """返回管理器的字符串表示"""
        return f"<QdrantManager(url='{self.url}')>"
