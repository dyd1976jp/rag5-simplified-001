"""
混合搜索工具模块

提供混合搜索功能，结合向量搜索和关键词搜索，提高检索召回率。
"""

import logging
import re
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

from rag5.config import settings
from rag5.tools.embeddings import OllamaEmbeddingsManager
from rag5.tools.vectordb import QdrantManager

logger = logging.getLogger(__name__)


class HybridSearchTool:
    """
    混合搜索工具
    
    结合向量搜索和关键词搜索，通过加权合并提高检索效果。
    向量搜索捕获语义相似性，关键词搜索确保精确匹配。
    
    属性:
        embeddings_manager: 嵌入模型管理器
        qdrant_manager: Qdrant 向量数据库管理器
        collection_name: 集合名称
    
    示例:
        >>> from rag5.tools.search import HybridSearchTool
        >>> from rag5.tools.embeddings import OllamaEmbeddingsManager
        >>> from rag5.tools.vectordb import QdrantManager
        >>> 
        >>> embeddings = OllamaEmbeddingsManager(model="bge-m3")
        >>> qdrant = QdrantManager(url="http://localhost:6333")
        >>> 
        >>> tool = HybridSearchTool(embeddings, qdrant, "knowledge_base")
        >>> results = tool.hybrid_search(
        ...     query="于朦朧是怎么死的",
        ...     vector_weight=0.7,
        ...     keyword_weight=0.3
        ... )
    """
    
    def __init__(
        self,
        embeddings_manager: OllamaEmbeddingsManager,
        qdrant_manager: QdrantManager,
        collection_name: str
    ):
        """
        初始化混合搜索工具
        
        参数:
            embeddings_manager: 嵌入模型管理器
            qdrant_manager: Qdrant 向量数据库管理器
            collection_name: 集合名称
        """
        self.embeddings_manager = embeddings_manager
        self.qdrant_manager = qdrant_manager
        self.collection_name = collection_name
        logger.debug(f"初始化混合搜索工具，集合: {collection_name}")
    
    def hybrid_search(
        self,
        query: str,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        keyword_boost: float = 1.5
    ) -> List[Dict[str, Any]]:
        """
        混合搜索：结合向量搜索和关键词搜索
        
        参数:
            query: 查询文本
            vector_weight: 向量搜索权重（0-1）
            keyword_weight: 关键词搜索权重（0-1）
            top_k: 返回结果数量（默认使用配置中的值）
            score_threshold: 相似度阈值（默认使用配置中的值）
            keyword_boost: 关键词匹配的额外加权系数
        
        返回:
            搜索结果列表，每个结果包含 score, content, source, metadata, match_type
        
        示例:
            >>> tool = HybridSearchTool(embeddings, qdrant, "knowledge_base")
            >>> results = tool.hybrid_search(
            ...     query="于朦朧",
            ...     vector_weight=0.7,
            ...     keyword_weight=0.3
            ... )
            >>> for result in results:
            ...     print(f"Score: {result['score']}, Type: {result['match_type']}")
        """
        # 使用配置中的默认值
        if top_k is None:
            top_k = settings.top_k
        if score_threshold is None:
            score_threshold = settings.similarity_threshold
        
        # 归一化权重
        total_weight = vector_weight + keyword_weight
        if total_weight > 0:
            vector_weight = vector_weight / total_weight
            keyword_weight = keyword_weight / total_weight
        else:
            logger.warning("权重总和为0，使用默认权重 (0.7, 0.3)")
            vector_weight = 0.7
            keyword_weight = 0.3
        
        logger.info("=" * 60)
        logger.info("开始混合搜索")
        logger.info(f"查询: {query}")
        logger.info(f"向量权重: {vector_weight:.2f}, 关键词权重: {keyword_weight:.2f}")
        logger.info(f"Top K: {top_k}, 阈值: {score_threshold}")
        logger.info("=" * 60)
        
        # 执行向量搜索
        logger.info("\n[步骤 1/3] 执行向量搜索...")
        vector_results = self._vector_search(
            query=query,
            limit=top_k * 2,  # 获取更多结果用于合并
            score_threshold=score_threshold * 0.8  # 降低阈值以获取更多候选
        )
        logger.info(f"✓ 向量搜索找到 {len(vector_results)} 个结果")
        
        # 执行关键词搜索
        logger.info("\n[步骤 2/3] 执行关键词搜索...")
        keyword_results = self._keyword_search(
            query=query,
            limit=top_k * 2
        )
        logger.info(f"✓ 关键词搜索找到 {len(keyword_results)} 个结果")
        
        # 合并和重排序结果
        logger.info("\n[步骤 3/3] 合并和重排序结果...")
        merged_results = self._merge_results(
            vector_results=vector_results,
            keyword_results=keyword_results,
            vector_weight=vector_weight,
            keyword_weight=keyword_weight,
            keyword_boost=keyword_boost,
            top_k=top_k
        )
        
        logger.info("=" * 60)
        logger.info(f"混合搜索完成，返回 {len(merged_results)} 个结果")
        logger.info("=" * 60)
        
        return merged_results
    
    def _vector_search(
        self,
        query: str,
        limit: int,
        score_threshold: float
    ) -> List[Dict[str, Any]]:
        """
        执行向量搜索
        
        参数:
            query: 查询文本
            limit: 返回结果数量
            score_threshold: 相似度阈值
        
        返回:
            搜索结果列表
        """
        try:
            # 向量化查询
            query_vector = self.embeddings_manager.embed_query(query)
            logger.debug(f"查询向量维度: {len(query_vector)}")
            
            # 执行搜索
            search_results = self.qdrant_manager.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # 格式化结果
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "id": str(result.id),
                    "score": float(result.score),
                    "content": result.payload.get("text", ""),
                    "source": result.payload.get("source", "unknown"),
                    "metadata": result.payload.get("metadata", {}),
                    "match_type": "vector"
                })
            
            if formatted_results:
                scores = [r["score"] for r in formatted_results]
                logger.debug(
                    f"向量搜索分数范围: {min(scores):.4f} - {max(scores):.4f}"
                )
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}", exc_info=True)
            return []
    
    def _keyword_search(
        self,
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        执行关键词搜索（通过payload过滤）
        
        从向量数据库中获取所有点，然后在内存中进行关键词匹配。
        这是一个简化实现，适用于中小规模数据集。
        
        参数:
            query: 查询文本
            limit: 返回结果数量
        
        返回:
            搜索结果列表
        """
        try:
            # 提取关键词
            keywords = self._extract_keywords(query)
            if not keywords:
                logger.debug("未提取到关键词，跳过关键词搜索")
                return []
            
            logger.debug(f"提取的关键词: {keywords}")
            
            # 获取集合中的所有点（使用滚动方式）
            # 注意：这是简化实现，对于大规模数据集应使用更高效的方法
            all_points = self._scroll_collection(limit=1000)
            
            if not all_points:
                logger.debug("集合中没有数据点")
                return []
            
            logger.debug(f"检查 {len(all_points)} 个数据点")
            
            # 在内存中进行关键词匹配
            matched_results = []
            for point in all_points:
                text = point.payload.get("text", "")
                if not text:
                    continue
                
                # 计算关键词匹配分数
                match_score = self._calculate_keyword_score(text, keywords)
                
                if match_score > 0:
                    matched_results.append({
                        "id": str(point.id),
                        "score": match_score,
                        "content": text,
                        "source": point.payload.get("source", "unknown"),
                        "metadata": point.payload.get("metadata", {}),
                        "match_type": "keyword"
                    })
            
            # 按分数排序并返回前N个
            matched_results.sort(key=lambda x: x["score"], reverse=True)
            top_results = matched_results[:limit]
            
            if top_results:
                logger.debug(
                    f"关键词匹配: {len(matched_results)} 个结果, "
                    f"返回前 {len(top_results)} 个"
                )
            
            return top_results
            
        except Exception as e:
            logger.error(f"关键词搜索失败: {e}", exc_info=True)
            return []
    
    def _scroll_collection(self, limit: int = 1000) -> List[Any]:
        """
        滚动获取集合中的所有点
        
        参数:
            limit: 最大获取数量
        
        返回:
            数据点列表
        """
        try:
            # 使用 scroll 方法获取数据点
            points, _ = self.qdrant_manager.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                with_payload=True,
                with_vectors=False  # 不需要向量数据
            )
            return points
        except Exception as e:
            logger.error(f"滚动获取数据点失败: {e}")
            return []
    
    def _extract_keywords(self, query: str) -> Set[str]:
        """
        从查询中提取关键词
        
        参数:
            query: 查询文本
        
        返回:
            关键词集合
        """
        # 移除标点符号和特殊字符
        cleaned_query = re.sub(r'[^\w\s]', ' ', query)
        
        # 分词（简单按空格分割，对中文按字符分割）
        words = set()
        
        # 提取英文单词
        english_words = re.findall(r'[a-zA-Z]+', cleaned_query)
        words.update(w.lower() for w in english_words if len(w) > 2)
        
        # 提取中文字符（2字及以上的组合）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', query)
        for chars in chinese_chars:
            if len(chars) >= 2:
                words.add(chars)
            # 也添加单个字符（对于人名等）
            for char in chars:
                words.add(char)
        
        return words
    
    def _calculate_keyword_score(self, text: str, keywords: Set[str]) -> float:
        """
        计算文本的关键词匹配分数
        
        参数:
            text: 文本内容
            keywords: 关键词集合
        
        返回:
            匹配分数（0-1）
        """
        if not keywords or not text:
            return 0.0
        
        text_lower = text.lower()
        matched_count = 0
        total_matches = 0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # 计算关键词出现次数
            count = text_lower.count(keyword_lower)
            if count > 0:
                matched_count += 1
                total_matches += count
        
        # 计算分数：匹配关键词比例 + 总匹配次数的加权
        keyword_ratio = matched_count / len(keywords)
        frequency_bonus = min(total_matches * 0.1, 0.5)  # 最多加0.5分
        
        score = keyword_ratio * 0.7 + frequency_bonus
        return min(score, 1.0)  # 限制在0-1范围内
    
    def _merge_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        vector_weight: float,
        keyword_weight: float,
        keyword_boost: float,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        合并和重排序向量搜索和关键词搜索的结果
        
        参数:
            vector_results: 向量搜索结果
            keyword_results: 关键词搜索结果
            vector_weight: 向量搜索权重
            keyword_weight: 关键词搜索权重
            keyword_boost: 关键词匹配的额外加权系数
            top_k: 返回结果数量
        
        返回:
            合并后的结果列表
        """
        # 使用字典存储合并结果，key为文档ID
        merged_dict = {}
        
        # 添加向量搜索结果
        for result in vector_results:
            doc_id = result["id"]
            merged_dict[doc_id] = {
                **result,
                "vector_score": result["score"],
                "keyword_score": 0.0,
                "final_score": result["score"] * vector_weight,
                "match_type": "vector"
            }
        
        # 合并关键词搜索结果
        for result in keyword_results:
            doc_id = result["id"]
            keyword_score = result["score"]
            
            if doc_id in merged_dict:
                # 文档同时出现在两个结果中
                merged_dict[doc_id]["keyword_score"] = keyword_score
                merged_dict[doc_id]["final_score"] = (
                    merged_dict[doc_id]["vector_score"] * vector_weight +
                    keyword_score * keyword_weight * keyword_boost
                )
                merged_dict[doc_id]["match_type"] = "hybrid"
                
                logger.debug(
                    f"混合匹配 (ID: {doc_id}): "
                    f"向量={merged_dict[doc_id]['vector_score']:.4f}, "
                    f"关键词={keyword_score:.4f}, "
                    f"最终={merged_dict[doc_id]['final_score']:.4f}"
                )
            else:
                # 仅关键词匹配
                merged_dict[doc_id] = {
                    **result,
                    "vector_score": 0.0,
                    "keyword_score": keyword_score,
                    "final_score": keyword_score * keyword_weight * keyword_boost,
                    "match_type": "keyword"
                }
        
        # 转换为列表并按最终分数排序
        merged_results = list(merged_dict.values())
        merged_results.sort(key=lambda x: x["final_score"], reverse=True)
        
        # 返回前K个结果
        top_results = merged_results[:top_k]
        
        # 记录统计信息
        match_types = defaultdict(int)
        for result in top_results:
            match_types[result["match_type"]] += 1
        
        logger.info(
            f"✓ 合并完成: 总计 {len(merged_results)} 个唯一结果, "
            f"返回前 {len(top_results)} 个"
        )
        logger.info(
            f"匹配类型分布: "
            f"向量={match_types['vector']}, "
            f"关键词={match_types['keyword']}, "
            f"混合={match_types['hybrid']}"
        )
        
        # 清理结果，移除内部字段
        for result in top_results:
            result["score"] = result["final_score"]
            # 保留 vector_score, keyword_score 用于调试
        
        return top_results
