"""
向量存储管理器

管理知识库的向量集合，提供集合创建、删除、数据插入和搜索功能。
"""

import logging
import uuid
from typing import List, Dict, Any, Optional

from qdrant_client.models import (
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)

from rag5.tools.vectordb.qdrant_client import QdrantManager

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    向量存储管理器
    
    为知识库管理向量集合，每个知识库对应一个独立的集合。
    提供集合生命周期管理、数据插入和搜索功能。
    
    属性:
        qdrant_manager: Qdrant 管理器实例
        collection_cache: 集合存在性缓存
    
    示例:
        >>> from rag5.core.knowledge_base.vector_manager import VectorStoreManager
        >>> from rag5.tools.vectordb import QdrantManager
        >>>
        >>> qdrant = QdrantManager("http://localhost:6333")
        >>> manager = VectorStoreManager(qdrant)
        >>> 
        >>> # 创建集合
        >>> await manager.create_collection("kb_123", embedding_dimension=1024)
        >>> 
        >>> # 插入数据
        >>> chunks = [{"id": "1", "text": "内容", "file_id": "f1"}]
        >>> embeddings = [[0.1, 0.2, ...]]
        >>> await manager.insert_chunks("kb_123", chunks, embeddings)
        >>> 
        >>> # 搜索
        >>> results = await manager.search("kb_123", query_vector, top_k=5)
    """
    
    def __init__(self, qdrant_manager: QdrantManager):
        """
        初始化向量存储管理器
        
        参数:
            qdrant_manager: Qdrant 管理器实例
        """
        self.qdrant_manager = qdrant_manager
        self.collection_cache: Dict[str, bool] = {}
        logger.debug("初始化向量存储管理器")
    
    async def create_collection(
        self,
        kb_id: str,
        embedding_dimension: int,
        distance: Distance = Distance.COSINE
    ) -> None:
        """
        为知识库创建向量集合
        
        集合名称使用知识库 ID，确保每个知识库有独立的向量空间。
        
        参数:
            kb_id: 知识库 ID（用作集合名称）
            embedding_dimension: 向量维度
            distance: 距离度量方式（默认为余弦距离）
        
        异常:
            Exception: 集合创建失败
        
        示例:
            >>> await manager.create_collection("kb_abc123", 1024)
        """
        try:
            logger.info(f"为知识库 {kb_id} 创建向量集合")
            logger.debug(f"集合参数 - 维度: {embedding_dimension}, 距离: {distance}")
            
            # 使用 QdrantManager 的 ensure_collection 方法
            self.qdrant_manager.ensure_collection(
                collection_name=kb_id,
                vector_dim=embedding_dimension,
                distance=distance
            )
            
            # 更新缓存
            self.collection_cache[kb_id] = True
            
            logger.info(f"✓ 知识库 {kb_id} 的向量集合创建成功")
        except Exception as e:
            logger.error(f"创建向量集合失败: {e}", exc_info=True)
            raise
    
    async def delete_collection(self, kb_id: str) -> bool:
        """
        删除知识库的向量集合
        
        参数:
            kb_id: 知识库 ID
        
        返回:
            是否成功删除
        
        示例:
            >>> success = await manager.delete_collection("kb_abc123")
        """
        try:
            logger.info(f"删除知识库 {kb_id} 的向量集合")
            
            # 检查集合是否存在
            if not await self.collection_exists(kb_id):
                logger.warning(f"集合 {kb_id} 不存在，无需删除")
                return True
            
            # 删除集合
            success = self.qdrant_manager.delete_collection(kb_id)
            
            # 清除缓存
            self.collection_cache.pop(kb_id, None)
            
            if success:
                logger.info(f"✓ 知识库 {kb_id} 的向量集合已删除")
            else:
                logger.error(f"删除知识库 {kb_id} 的向量集合失败")
            
            return success
        except Exception as e:
            logger.error(f"删除向量集合时出错: {e}", exc_info=True)
            return False
    
    async def collection_exists(self, kb_id: str) -> bool:
        """
        检查知识库的向量集合是否存在
        
        使用缓存提高性能，避免频繁查询。
        
        参数:
            kb_id: 知识库 ID
        
        返回:
            集合是否存在
        
        示例:
            >>> exists = await manager.collection_exists("kb_abc123")
        """
        # 先检查缓存
        if kb_id in self.collection_cache:
            logger.debug(f"从缓存获取集合 {kb_id} 的存在性: {self.collection_cache[kb_id]}")
            return self.collection_cache[kb_id]
        
        # 查询实际状态
        exists = self.qdrant_manager.collection_exists(kb_id)
        
        # 更新缓存
        self.collection_cache[kb_id] = exists
        
        logger.debug(f"集合 {kb_id} 存在性: {exists}")
        return exists
    
    async def insert_chunks(
        self,
        kb_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> int:
        """
        批量插入文档块到知识库的向量集合
        
        参数:
            kb_id: 知识库 ID
            chunks: 文档块列表，每个块包含 id, text, file_id 等字段
            embeddings: 对应的向量嵌入列表
        
        返回:
            成功插入的块数量
        
        异常:
            ValueError: 块数量与向量数量不匹配
            Exception: 插入失败
        
        示例:
            >>> chunks = [
            ...     {"id": "chunk_1", "text": "内容1", "file_id": "f1", "source": "doc.pdf"},
            ...     {"id": "chunk_2", "text": "内容2", "file_id": "f1", "source": "doc.pdf"}
            ... ]
            >>> embeddings = [[0.1, 0.2, ...], [0.3, 0.4, ...]]
            >>> count = await manager.insert_chunks("kb_abc123", chunks, embeddings)
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"块数量 ({len(chunks)}) 与向量数量 ({len(embeddings)}) 不匹配"
            )
        
        if not chunks:
            logger.warning("没有要插入的块")
            return 0
        
        try:
            logger.info(f"向知识库 {kb_id} 插入 {len(chunks)} 个文档块")
            
            # 检查集合是否存在
            if not await self.collection_exists(kb_id):
                raise ValueError(f"知识库 {kb_id} 的向量集合不存在")
            
            # 构建 PointStruct 列表
            points = []
            for chunk, embedding in zip(chunks, embeddings):
                # 确保每个块都有唯一 ID
                chunk_id = chunk.get("id")
                if not chunk_id:
                    chunk_id = str(uuid.uuid4())
                    chunk["id"] = chunk_id

                # 将字符串 ID 转换为 UUID（Qdrant 要求 ID 是 UUID 或整数）
                # 如果 chunk_id 是字符串格式（如 "file_xxx_chunk_0"），则生成 UUID
                try:
                    # 尝试将其解析为 UUID
                    point_id = uuid.UUID(chunk_id)
                except (ValueError, AttributeError):
                    # 如果不是有效的 UUID，则使用字符串的 hash 生成一个确定性的 UUID
                    # 这样相同的 chunk_id 总是会生成相同的 UUID
                    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
                    point_id = uuid.uuid5(namespace, chunk_id)

                # 创建 payload（包含所有块的元数据，包括原始的 chunk_id）
                payload = {
                    "chunk_id": chunk_id,  # 保存原始的字符串 ID 用于追踪
                    "text": chunk.get("text", ""),
                    "file_id": chunk.get("file_id", ""),
                    "source": chunk.get("source", ""),
                    "chunk_index": chunk.get("chunk_index", 0),
                    "kb_id": kb_id,  # 添加知识库 ID 用于过滤
                }

                # 添加其他元数据
                for key, value in chunk.items():
                    if key not in payload and key != "id":
                        payload[key] = value

                points.append(
                    PointStruct(
                        id=str(point_id),  # 转换为字符串形式的 UUID
                        vector=embedding,
                        payload=payload
                    )
                )
            
            # 批量上传
            self.qdrant_manager.upsert(
                collection_name=kb_id,
                points=points
            )
            
            logger.info(f"✓ 成功插入 {len(points)} 个文档块到知识库 {kb_id}")
            return len(points)
        except Exception as e:
            logger.error(f"插入文档块失败: {e}", exc_info=True)
            raise
    
    async def delete_by_file_id(self, kb_id: str, file_id: str) -> bool:
        """
        删除指定文件的所有文档块
        
        参数:
            kb_id: 知识库 ID
            file_id: 文件 ID
        
        返回:
            是否成功删除
        
        示例:
            >>> success = await manager.delete_by_file_id("kb_abc123", "file_xyz")
        """
        try:
            logger.info(f"从知识库 {kb_id} 删除文件 {file_id} 的所有块")
            
            # 检查集合是否存在
            if not await self.collection_exists(kb_id):
                logger.warning(f"集合 {kb_id} 不存在")
                return True
            
            # 构建过滤器
            delete_filter = Filter(
                must=[
                    FieldCondition(
                        key="file_id",
                        match=MatchValue(value=file_id)
                    )
                ]
            )
            
            # 执行删除
            self.qdrant_manager.client.delete(
                collection_name=kb_id,
                points_selector=delete_filter
            )
            
            logger.info(f"✓ 成功删除文件 {file_id} 的所有块")
            return True
        except Exception as e:
            logger.error(f"删除文件块失败: {e}", exc_info=True)
            return False
    
    async def search(
        self,
        kb_id: str,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        query_filter: Optional[Filter] = None
    ) -> List[Dict[str, Any]]:
        """
        在知识库中搜索相似文档块
        
        参数:
            kb_id: 知识库 ID
            query_vector: 查询向量
            top_k: 返回结果数量
            score_threshold: 相似度阈值（可选）
            query_filter: 额外的查询过滤器（可选）
        
        返回:
            搜索结果列表，每个结果包含 id, score, payload
        
        异常:
            ValueError: 集合不存在
            Exception: 搜索失败
        
        示例:
            >>> results = await manager.search(
            ...     "kb_abc123",
            ...     query_vector=[0.1, 0.2, ...],
            ...     top_k=5,
            ...     score_threshold=0.3
            ... )
            >>> for result in results:
            ...     print(f"Score: {result['score']}, Text: {result['payload']['text']}")
        """
        try:
            logger.info(f"在知识库 {kb_id} 中搜索")
            logger.debug(f"搜索参数 - top_k: {top_k}, threshold: {score_threshold}")
            
            # 检查集合是否存在
            if not await self.collection_exists(kb_id):
                raise ValueError(f"知识库 {kb_id} 的向量集合不存在")
            
            # 执行搜索
            scored_points = self.qdrant_manager.search(
                collection_name=kb_id,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            # 转换结果格式
            results = []
            for point in scored_points:
                results.append({
                    "id": point.id,
                    "score": point.score,
                    "payload": point.payload
                })
            
            logger.info(f"✓ 搜索完成，找到 {len(results)} 个结果")
            
            # 记录结果统计
            if results:
                scores = [r["score"] for r in results]
                logger.debug(
                    f"相似度分数范围: {min(scores):.4f} - {max(scores):.4f}, "
                    f"平均: {sum(scores)/len(scores):.4f}"
                )
            
            return results
        except Exception as e:
            logger.error(f"搜索失败: {e}", exc_info=True)
            raise
    
    def get_collection_stats(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """
        获取知识库向量集合的统计信息
        
        参数:
            kb_id: 知识库 ID
        
        返回:
            统计信息字典，包含 vectors_count, points_count, status
        
        示例:
            >>> stats = manager.get_collection_stats("kb_abc123")
            >>> print(f"向量数量: {stats['vectors_count']}")
        """
        try:
            return self.qdrant_manager.get_collection_info(kb_id)
        except Exception as e:
            logger.error(f"获取集合统计信息失败: {e}")
            return None
    
    def clear_cache(self) -> None:
        """
        清除集合存在性缓存
        
        在集合状态可能发生变化时调用。
        
        示例:
            >>> manager.clear_cache()
        """
        logger.debug("清除集合缓存")
        self.collection_cache.clear()
    
    def __repr__(self) -> str:
        """返回管理器的字符串表示"""
        return f"<VectorStoreManager(cached_collections={len(self.collection_cache)})>"
