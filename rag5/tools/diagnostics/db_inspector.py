"""
Qdrant 数据库检查器模块

提供向量数据库的诊断和验证功能。
"""

import logging
from typing import Dict, Any, List, Optional
from qdrant_client.models import ScoredPoint
import time

logger = logging.getLogger(__name__)


class QdrantInspector:
    """
    Qdrant 数据库检查器
    
    提供集合统计、关键词搜索、样本数据获取和嵌入验证功能。
    
    属性:
        qdrant_manager: Qdrant 管理器实例
        embeddings_manager: 嵌入模型管理器实例（可选）
    
    示例:
        >>> from rag5.tools.vectordb import QdrantManager
        >>> from rag5.tools.diagnostics import QdrantInspector
        >>>
        >>> qdrant = QdrantManager("http://localhost:6333")
        >>> inspector = QdrantInspector(qdrant)
        >>> stats = inspector.get_collection_stats("knowledge_base")
        >>> print(f"集合中有 {stats['points_count']} 个点")
    """
    
    def __init__(self, qdrant_manager, embeddings_manager=None):
        """
        初始化数据库检查器
        
        参数:
            qdrant_manager: QdrantManager 实例
            embeddings_manager: OllamaEmbeddingsManager 实例（可选，用于嵌入验证）
        """
        self.qdrant_manager = qdrant_manager
        self.embeddings_manager = embeddings_manager
        logger.debug("初始化 Qdrant 数据库检查器")
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        获取集合统计信息
        
        参数:
            collection_name: 集合名称
        
        返回:
            {
                "points_count": int,  # 点数量
                "vectors_count": int,  # 向量数量
                "indexed_vectors_count": int,  # 已索引向量数量
                "status": str,  # 集合状态
                "exists": bool  # 集合是否存在
            }
        
        示例:
            >>> inspector = QdrantInspector(qdrant_manager)
            >>> stats = inspector.get_collection_stats("knowledge_base")
            >>> if stats['exists']:
            ...     print(f"集合状态: {stats['status']}")
            ...     print(f"点数量: {stats['points_count']}")
        """
        try:
            # 检查集合是否存在
            if not self.qdrant_manager.collection_exists(collection_name):
                logger.warning(f"集合 '{collection_name}' 不存在")
                return {
                    "exists": False,
                    "points_count": 0,
                    "vectors_count": 0,
                    "indexed_vectors_count": 0,
                    "status": "not_found"
                }
            
            # 获取集合信息
            collection = self.qdrant_manager.client.get_collection(collection_name)
            
            stats = {
                "exists": True,
                "points_count": collection.points_count,
                "vectors_count": collection.vectors_count or collection.points_count,
                "indexed_vectors_count": collection.indexed_vectors_count or 0,
                "status": collection.status.value if hasattr(collection.status, 'value') else str(collection.status)
            }
            
            logger.info(
                f"集合 '{collection_name}' 统计: "
                f"points={stats['points_count']}, "
                f"vectors={stats['vectors_count']}, "
                f"status={stats['status']}"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"获取集合统计信息失败: {e}")
            return {
                "exists": False,
                "points_count": 0,
                "vectors_count": 0,
                "indexed_vectors_count": 0,
                "status": "error",
                "error": str(e)
            }
    
    def search_by_keyword(
        self,
        collection_name: str,
        keyword: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        通过关键词搜索（遍历所有点的 payload）
        
        参数:
            collection_name: 集合名称
            keyword: 搜索关键词
            limit: 返回结果数量限制
        
        返回:
            [
                {
                    "id": str,  # 点 ID
                    "text": str,  # 文本内容
                    "source": str,  # 文档来源
                    "contains_keyword": bool,  # 是否包含关键词
                    "keyword_count": int  # 关键词出现次数
                }
            ]
        
        示例:
            >>> inspector = QdrantInspector(qdrant_manager)
            >>> results = inspector.search_by_keyword("knowledge_base", "于朦朧")
            >>> for result in results:
            ...     print(f"找到: {result['source']}, 出现 {result['keyword_count']} 次")
        """
        try:
            logger.info(f"在集合 '{collection_name}' 中搜索关键词: '{keyword}'")
            
            # 检查集合是否存在
            if not self.qdrant_manager.collection_exists(collection_name):
                logger.warning(f"集合 '{collection_name}' 不存在")
                return []
            
            # 使用 scroll 方法遍历所有点
            results = []
            offset = None
            batch_size = 100
            total_checked = 0
            
            while True:
                # 获取一批点
                records, next_offset = self.qdrant_manager.client.scroll(
                    collection_name=collection_name,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                if not records:
                    break
                
                # 检查每个点的 payload
                for record in records:
                    total_checked += 1
                    payload = record.payload or {}
                    text = payload.get('text', '')
                    source = payload.get('source', 'unknown')
                    
                    # 检查是否包含关键词
                    if keyword in text:
                        keyword_count = text.count(keyword)
                        results.append({
                            "id": str(record.id),
                            "text": text[:200] + "..." if len(text) > 200 else text,
                            "full_text": text,
                            "source": source,
                            "contains_keyword": True,
                            "keyword_count": keyword_count
                        })
                        
                        logger.debug(
                            f"找到匹配: id={record.id}, source={source}, "
                            f"count={keyword_count}"
                        )
                        
                        # 达到限制数量则停止
                        if len(results) >= limit:
                            break
                
                # 达到限制数量则停止
                if len(results) >= limit:
                    break
                
                # 检查是否还有更多数据
                if next_offset is None:
                    break
                
                offset = next_offset
            
            logger.info(
                f"搜索完成: 检查了 {total_checked} 个点, "
                f"找到 {len(results)} 个包含关键词 '{keyword}' 的结果"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"关键词搜索失败: {e}")
            return []
    
    def get_sample_points(
        self,
        collection_name: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取样本数据点
        
        参数:
            collection_name: 集合名称
            limit: 样本数量
        
        返回:
            [
                {
                    "id": str,  # 点 ID
                    "vector_dim": int,  # 向量维度
                    "payload": dict,  # payload 数据
                    "has_text": bool,  # 是否有文本
                    "has_source": bool  # 是否有来源
                }
            ]
        
        示例:
            >>> inspector = QdrantInspector(qdrant_manager)
            >>> samples = inspector.get_sample_points("knowledge_base", limit=3)
            >>> for sample in samples:
            ...     print(f"ID: {sample['id']}, 维度: {sample['vector_dim']}")
        """
        try:
            logger.info(f"获取集合 '{collection_name}' 的样本数据 (limit={limit})")
            
            # 检查集合是否存在
            if not self.qdrant_manager.collection_exists(collection_name):
                logger.warning(f"集合 '{collection_name}' 不存在")
                return []
            
            # 使用 scroll 获取样本点
            records, _ = self.qdrant_manager.client.scroll(
                collection_name=collection_name,
                limit=limit,
                with_payload=True,
                with_vectors=True
            )
            
            samples = []
            for record in records:
                payload = record.payload or {}
                vector = record.vector
                
                # 获取向量维度
                if isinstance(vector, dict):
                    # 命名向量
                    vector_dim = len(list(vector.values())[0]) if vector else 0
                else:
                    # 单一向量
                    vector_dim = len(vector) if vector else 0
                
                sample = {
                    "id": str(record.id),
                    "vector_dim": vector_dim,
                    "payload": payload,
                    "has_text": 'text' in payload and bool(payload['text']),
                    "has_source": 'source' in payload and bool(payload['source']),
                    "text_preview": payload.get('text', '')[:100] if 'text' in payload else None
                }
                
                samples.append(sample)
                
                logger.debug(
                    f"样本 {record.id}: dim={vector_dim}, "
                    f"has_text={sample['has_text']}, has_source={sample['has_source']}"
                )
            
            logger.info(f"获取了 {len(samples)} 个样本数据点")
            return samples
            
        except Exception as e:
            logger.error(f"获取样本数据失败: {e}")
            return []
    
    def verify_embeddings(
        self,
        collection_name: str,
        test_texts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        验证嵌入模型是否正常工作
        
        参数:
            collection_name: 集合名称
            test_texts: 测试文本列表（可选，默认使用内置测试文本）
        
        返回:
            {
                "model_working": bool,  # 模型是否正常工作
                "model_name": str,  # 模型名称
                "vector_dim": int,  # 向量维度
                "expected_dim": int,  # 期望的向量维度
                "dimension_match": bool,  # 维度是否匹配
                "test_results": List[dict],  # 测试结果列表
                "average_time": float,  # 平均生成时间（秒）
                "error": str  # 错误信息（如果有）
            }
        
        示例:
            >>> inspector = QdrantInspector(qdrant_manager, embeddings_manager)
            >>> result = inspector.verify_embeddings("knowledge_base")
            >>> if result['model_working']:
            ...     print(f"模型正常，向量维度: {result['vector_dim']}")
            ... else:
            ...     print(f"模型异常: {result.get('error')}")
        """
        if self.embeddings_manager is None:
            logger.warning("未提供嵌入模型管理器，无法验证嵌入")
            return {
                "model_working": False,
                "error": "未提供嵌入模型管理器"
            }
        
        # 默认测试文本
        if test_texts is None:
            test_texts = [
                "这是一个测试文本",
                "人工智能是什么？",
                "于朦朧是谁？"
            ]
        
        try:
            logger.info("验证嵌入模型...")
            
            # 获取集合的期望向量维度
            expected_dim = 0
            if self.qdrant_manager.collection_exists(collection_name):
                collection = self.qdrant_manager.client.get_collection(collection_name)
                # 获取向量配置
                if hasattr(collection.config, 'params'):
                    vector_config = collection.config.params.vectors
                    if isinstance(vector_config, dict):
                        # 命名向量
                        expected_dim = list(vector_config.values())[0].size
                    else:
                        # 单一向量
                        expected_dim = vector_config.size
            
            # 测试每个文本
            test_results = []
            total_time = 0
            
            for text in test_texts:
                try:
                    start_time = time.time()
                    vector = self.embeddings_manager.embed_query(text)
                    elapsed_time = time.time() - start_time
                    total_time += elapsed_time
                    
                    test_results.append({
                        "text": text,
                        "success": True,
                        "vector_dim": len(vector),
                        "time": elapsed_time,
                        "error": None
                    })
                    
                    logger.debug(
                        f"测试文本 '{text[:20]}...': "
                        f"dim={len(vector)}, time={elapsed_time:.3f}s"
                    )
                    
                except Exception as e:
                    test_results.append({
                        "text": text,
                        "success": False,
                        "vector_dim": 0,
                        "time": 0,
                        "error": str(e)
                    })
                    logger.error(f"测试文本 '{text[:20]}...' 失败: {e}")
            
            # 检查是否所有测试都成功
            all_success = all(r['success'] for r in test_results)
            
            # 获取向量维度（从第一个成功的测试）
            vector_dim = 0
            for result in test_results:
                if result['success']:
                    vector_dim = result['vector_dim']
                    break
            
            # 检查维度是否匹配
            dimension_match = (vector_dim == expected_dim) if expected_dim > 0 else True
            
            # 计算平均时间
            avg_time = total_time / len(test_texts) if test_texts else 0
            
            result = {
                "model_working": all_success and dimension_match,
                "model_name": self.embeddings_manager.model,
                "vector_dim": vector_dim,
                "expected_dim": expected_dim,
                "dimension_match": dimension_match,
                "test_results": test_results,
                "average_time": avg_time,
                "total_tests": len(test_texts),
                "successful_tests": sum(1 for r in test_results if r['success'])
            }
            
            if result['model_working']:
                logger.info(
                    f"✓ 嵌入模型验证成功: {result['model_name']}, "
                    f"维度={vector_dim}, 平均时间={avg_time:.3f}s"
                )
            else:
                error_msg = []
                if not all_success:
                    error_msg.append("部分测试失败")
                if not dimension_match:
                    error_msg.append(
                        f"维度不匹配 (期望={expected_dim}, 实际={vector_dim})"
                    )
                result['error'] = ", ".join(error_msg)
                logger.warning(f"嵌入模型验证失败: {result['error']}")
            
            return result
            
        except Exception as e:
            logger.error(f"验证嵌入模型失败: {e}")
            return {
                "model_working": False,
                "model_name": self.embeddings_manager.model if self.embeddings_manager else "unknown",
                "vector_dim": 0,
                "expected_dim": expected_dim if 'expected_dim' in locals() else 0,
                "dimension_match": False,
                "test_results": [],
                "average_time": 0,
                "error": str(e)
            }
