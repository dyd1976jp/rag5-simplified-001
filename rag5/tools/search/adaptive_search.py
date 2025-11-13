"""
自适应搜索工具模块

提供自适应相似度阈值搜索功能，当初始阈值无足够结果时，动态降低阈值重新搜索。
"""

import logging
from typing import List, Dict, Any, Optional

from rag5.config import settings
from rag5.tools.embeddings import OllamaEmbeddingsManager
from rag5.tools.vectordb import QdrantManager

logger = logging.getLogger(__name__)


class AdaptiveSearchTool:
    """
    自适应搜索工具
    
    当初始相似度阈值无法返回足够结果时，自动降低阈值并重新搜索，
    直到找到足够的结果或达到最小阈值。
    
    属性:
        embeddings_manager: 嵌入模型管理器
        qdrant_manager: Qdrant 向量数据库管理器
        collection_name: 集合名称
    
    示例:
        >>> from rag5.tools.search import AdaptiveSearchTool
        >>> from rag5.tools.embeddings import OllamaEmbeddingsManager
        >>> from rag5.tools.vectordb import QdrantManager
        >>> 
        >>> embeddings = OllamaEmbeddingsManager(model="bge-m3")
        >>> qdrant = QdrantManager(url="http://localhost:6333")
        >>> 
        >>> tool = AdaptiveSearchTool(embeddings, qdrant, "knowledge_base")
        >>> results = tool.search_with_fallback(
        ...     query="于朦朧是怎么死的",
        ...     initial_threshold=0.7,
        ...     min_threshold=0.3,
        ...     target_results=3
        ... )
    """
    
    def __init__(
        self,
        embeddings_manager: OllamaEmbeddingsManager,
        qdrant_manager: QdrantManager,
        collection_name: str
    ):
        """
        初始化自适应搜索工具
        
        参数:
            embeddings_manager: 嵌入模型管理器
            qdrant_manager: Qdrant 向量数据库管理器
            collection_name: 集合名称
        """
        self.embeddings_manager = embeddings_manager
        self.qdrant_manager = qdrant_manager
        self.collection_name = collection_name
        logger.debug(f"初始化自适应搜索工具，集合: {collection_name}")
    
    def search_with_fallback(
        self,
        query: str,
        initial_threshold: Optional[float] = None,
        min_threshold: float = 0.1,
        target_results: int = 3,
        max_results: int = 10,
        threshold_step: float = 0.05
    ) -> List[Dict[str, Any]]:
        """
        使用回退策略的自适应搜索
        
        如果初始阈值没有足够结果，逐步降低阈值重新搜索，
        直到找到足够的结果或达到最小阈值。
        
        参数:
            query: 查询文本
            initial_threshold: 初始相似度阈值（默认使用配置中的值）
            min_threshold: 最小相似度阈值
            target_results: 目标结果数量
            max_results: 最大返回结果数量
            threshold_step: 每次降低的阈值步长
        
        返回:
            搜索结果列表，每个结果包含 score, content, source, metadata
        
        示例:
            >>> tool = AdaptiveSearchTool(embeddings, qdrant, "knowledge_base")
            >>> results = tool.search_with_fallback(
            ...     query="于朦朧",
            ...     initial_threshold=0.7,
            ...     min_threshold=0.3,
            ...     target_results=3
            ... )
            >>> for result in results:
            ...     print(f"Score: {result['score']}, Content: {result['content'][:50]}")
        """
        # 使用配置中的阈值作为默认值
        if initial_threshold is None:
            initial_threshold = settings.similarity_threshold
        
        logger.info("=" * 60)
        logger.info("开始自适应搜索")
        logger.info(f"查询: {query}")
        logger.info(f"初始阈值: {initial_threshold}")
        logger.info(f"最小阈值: {min_threshold}")
        logger.info(f"目标结果数: {target_results}")
        logger.info("=" * 60)
        
        # 验证参数
        if initial_threshold < min_threshold:
            logger.warning(
                f"初始阈值 ({initial_threshold}) 小于最小阈值 ({min_threshold})，"
                f"将使用最小阈值作为初始值"
            )
            initial_threshold = min_threshold
        
        # 向量化查询
        logger.info("\n[步骤 1/2] 向量化查询...")
        try:
            query_vector = self.embeddings_manager.embed_query(query)
            logger.info(f"✓ 查询向量化完成，维度: {len(query_vector)}")
        except Exception as e:
            logger.error(f"✗ 向量化查询失败: {e}", exc_info=True)
            return []
        
        # 自适应搜索
        logger.info("\n[步骤 2/2] 执行自适应搜索...")
        threshold = initial_threshold
        all_results = []
        attempt = 0
        
        while threshold >= min_threshold:
            attempt += 1
            logger.info(f"\n尝试 #{attempt}: 阈值 = {threshold:.3f}")
            
            try:
                # 执行搜索
                search_results = self.qdrant_manager.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=max_results,
                    score_threshold=threshold
                )
                
                logger.info(f"找到 {len(search_results)} 个结果")
                
                # 格式化结果
                formatted_results = self._format_results(search_results)
                
                # 如果找到足够的结果，返回
                if len(formatted_results) >= target_results:
                    logger.info(
                        f"✓ 成功找到 {len(formatted_results)} 个结果 "
                        f"(阈值: {threshold:.3f})"
                    )
                    logger.info("=" * 60)
                    return formatted_results[:max_results]
                
                # 保存当前结果
                all_results = formatted_results
                
                # 如果已经达到最小阈值，返回现有结果
                if threshold <= min_threshold:
                    logger.warning(
                        f"已达到最小阈值 ({min_threshold})，"
                        f"仅找到 {len(all_results)} 个结果"
                    )
                    break
                
                # 降低阈值
                new_threshold = max(threshold - threshold_step, min_threshold)
                logger.info(
                    f"结果不足 ({len(formatted_results)} < {target_results})，"
                    f"降低阈值: {threshold:.3f} -> {new_threshold:.3f}"
                )
                threshold = new_threshold
                
            except Exception as e:
                logger.error(f"✗ 搜索失败 (阈值: {threshold:.3f}): {e}", exc_info=True)
                # 尝试降低阈值继续搜索
                threshold = max(threshold - threshold_step, min_threshold)
                if threshold < min_threshold:
                    break
        
        # 返回找到的所有结果
        logger.info("=" * 60)
        if all_results:
            logger.info(
                f"自适应搜索完成，共找到 {len(all_results)} 个结果 "
                f"(最终阈值: {threshold:.3f})"
            )
        else:
            logger.warning(
                "自适应搜索未找到任何结果，建议:\n"
                "  1. 检查文档是否已正确索引\n"
                "  2. 尝试使用不同的查询词\n"
                "  3. 检查嵌入模型是否正常工作"
            )
        logger.info("=" * 60)
        
        return all_results
    
    def _format_results(self, results: List[Any]) -> List[Dict[str, Any]]:
        """
        格式化搜索结果
        
        参数:
            results: Qdrant 搜索结果列表
        
        返回:
            格式化后的结果列表
        """
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_result = {
                "score": float(result.score),
                "content": result.payload.get("text", ""),
                "source": result.payload.get("source", "unknown"),
                "metadata": result.payload.get("metadata", {})
            }
            formatted_results.append(formatted_result)
            
            # 记录每个结果的详细信息
            content_preview = result.payload.get("text", "")[:100]
            logger.debug(
                f"  结果 {i}: score={result.score:.4f}, "
                f"source={result.payload.get('source', 'unknown')}, "
                f"content_preview={content_preview}..."
            )
        
        return formatted_results
    
    def get_search_statistics(
        self,
        query: str,
        thresholds: List[float]
    ) -> Dict[str, Any]:
        """
        获取不同阈值下的搜索统计信息
        
        用于分析和调试，了解不同阈值对搜索结果的影响。
        
        参数:
            query: 查询文本
            thresholds: 要测试的阈值列表
        
        返回:
            统计信息字典
        
        示例:
            >>> tool = AdaptiveSearchTool(embeddings, qdrant, "knowledge_base")
            >>> stats = tool.get_search_statistics(
            ...     query="于朦朧",
            ...     thresholds=[0.7, 0.5, 0.3, 0.1]
            ... )
            >>> for threshold, count in stats['results_by_threshold'].items():
            ...     print(f"阈值 {threshold}: {count} 个结果")
        """
        logger.info(f"获取搜索统计信息: {query}")
        logger.info(f"测试阈值: {thresholds}")
        
        # 向量化查询
        try:
            query_vector = self.embeddings_manager.embed_query(query)
        except Exception as e:
            logger.error(f"向量化查询失败: {e}")
            return {
                "error": str(e),
                "results_by_threshold": {}
            }
        
        # 测试每个阈值
        results_by_threshold = {}
        for threshold in sorted(thresholds, reverse=True):
            try:
                search_results = self.qdrant_manager.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=100,  # 获取更多结果用于统计
                    score_threshold=threshold
                )
                results_by_threshold[threshold] = {
                    "count": len(search_results),
                    "scores": [float(r.score) for r in search_results],
                    "avg_score": sum(r.score for r in search_results) / len(search_results) if search_results else 0
                }
                logger.info(
                    f"阈值 {threshold:.3f}: {len(search_results)} 个结果, "
                    f"平均分数: {results_by_threshold[threshold]['avg_score']:.4f}"
                )
            except Exception as e:
                logger.error(f"测试阈值 {threshold} 时出错: {e}")
                results_by_threshold[threshold] = {
                    "count": 0,
                    "scores": [],
                    "avg_score": 0,
                    "error": str(e)
                }
        
        return {
            "query": query,
            "thresholds_tested": thresholds,
            "results_by_threshold": results_by_threshold
        }
