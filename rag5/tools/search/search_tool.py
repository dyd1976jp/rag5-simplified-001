"""
知识库搜索工具模块

提供知识库向量搜索功能，用于检索相关文档。
支持多知识库查询和向后兼容的默认知识库查询。
"""

import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool

from rag5.config import settings
from rag5.tools.embeddings import OllamaEmbeddingsManager
from rag5.tools.vectordb import QdrantManager
from rag5.utils.reflection_logger import AgentReflectionLogger

logger = logging.getLogger(__name__)

# 全局实例（延迟初始化）
_embeddings_manager: Optional[OllamaEmbeddingsManager] = None
_qdrant_manager: Optional[QdrantManager] = None
_reflection_logger: Optional[AgentReflectionLogger] = None
_kb_manager: Optional[Any] = None


def _get_embeddings_manager() -> OllamaEmbeddingsManager:
    """
    获取嵌入模型管理器实例（单例模式）

    返回:
        OllamaEmbeddingsManager 实例
    """
    global _embeddings_manager
    if _embeddings_manager is None:
        _embeddings_manager = OllamaEmbeddingsManager(
            model=settings.embed_model,
            base_url=settings.ollama_host
        )
        _embeddings_manager.initialize()
    return _embeddings_manager


def _get_qdrant_manager() -> QdrantManager:
    """
    获取 Qdrant 管理器实例（单例模式）

    返回:
        QdrantManager 实例
    """
    global _qdrant_manager
    if _qdrant_manager is None:
        _qdrant_manager = QdrantManager(url=settings.qdrant_url)
        # 确保集合存在
        _qdrant_manager.ensure_collection(
            collection_name=settings.collection_name,
            vector_dim=settings.vector_dim
        )
    return _qdrant_manager


def _get_reflection_logger() -> Optional[AgentReflectionLogger]:
    """
    获取反思日志记录器实例（如果启用）

    返回:
        AgentReflectionLogger 实例或 None
    """
    global _reflection_logger
    if _reflection_logger is None and settings.enable_reflection_logging:
        _reflection_logger = AgentReflectionLogger(
            log_file=settings.reflection_log_file
        )
    return _reflection_logger


def _get_kb_manager():
    """
    获取知识库管理器实例（单例模式）

    返回:
        KnowledgeBaseManager 实例或 None（如果初始化失败）
    """
    global _kb_manager
    if _kb_manager is None:
        try:
            from rag5.core.knowledge_base import KnowledgeBaseManager
            from rag5.core.knowledge_base.vector_manager import VectorStoreManager
            from rag5.tools.vectordb import QdrantManager
            from pathlib import Path
            
            # 初始化知识库管理器
            db_path = settings.kb_database_path if hasattr(settings, 'kb_database_path') else "data/knowledge_bases.db"
            file_storage_path = settings.kb_file_storage_path if hasattr(settings, 'kb_file_storage_path') else "docs"
            
            # 创建 Qdrant 管理器
            qdrant_manager = QdrantManager(url=settings.qdrant_url)
            
            # 创建向量存储管理器
            vector_manager = VectorStoreManager(qdrant_manager)
            
            _kb_manager = KnowledgeBaseManager(
                db_path=db_path,
                vector_manager=vector_manager,
                file_storage_path=file_storage_path
            )
            
            logger.info("✓ 知识库管理器已初始化")
        except Exception as e:
            logger.warning(f"无法初始化知识库管理器: {e}. 将使用传统搜索模式")
            _kb_manager = None
    
    return _kb_manager


def _format_search_results(results: List[Any]) -> List[Dict[str, Any]]:
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
            f"结果 {i}: score={result.score:.4f}, "
            f"source={result.payload.get('source', 'unknown')}, "
            f"content_preview={content_preview}..."
        )
    
    return formatted_results


def _search_with_kb_manager(
    query: str,
    kb_id: str,
    query_start_time: float,
    query_timestamp: str
) -> str:
    """
    使用知识库管理器进行搜索
    
    此函数使用指定知识库的配置（embedding_model, RetrievalConfig）
    进行搜索，提供更精确的知识库隔离和配置。
    
    参数:
        query: 搜索查询
        kb_id: 知识库 ID
        query_start_time: 查询开始时间
        query_timestamp: 查询时间戳
    
    返回:
        JSON 字符串，包含搜索结果
    """
    try:
        # 获取知识库管理器
        kb_manager = _get_kb_manager()
        
        if kb_manager is None:
            # 回退到传统搜索
            logger.warning(f"知识库管理器不可用，回退到传统搜索模式")
            error_output = {
                "error": "知识库管理器不可用，请使用默认搜索",
                "results": [],
                "total_count": 0
            }
            return json.dumps(error_output, ensure_ascii=False, indent=2)
        
        logger.info(f"\n[使用知识库管理器] 查询知识库: {kb_id}")
        
        # 使用知识库管理器查询
        # 这将使用知识库的 embedding_model 和 RetrievalConfig
        import asyncio
        
        # 运行异步查询
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                kb_manager.query_knowledge_base(
                    kb_id=kb_id,
                    query=query
                )
            )
        finally:
            loop.close()
        
        # 计算总耗时
        total_time = time.time() - query_start_time
        
        logger.info(f"✓ 知识库查询完成，找到 {len(results)} 个结果")
        logger.info(f"总耗时: {total_time:.3f}秒")
        
        # 获取知识库信息
        kb = kb_manager.db.get_kb(kb_id)
        kb_name = kb.name if kb else "unknown"
        
        # 格式化结果
        formatted_results = []
        for result in results:
            formatted_result = {
                "score": result.get("score", 0.0),
                "content": result.get("text", ""),
                "source": result.get("source", "unknown"),
                "metadata": result.get("metadata", {})
            }
            formatted_results.append(formatted_result)
        
        # 记录检索评估（如果启用反思日志）
        reflection_logger = _get_reflection_logger()
        if reflection_logger:
            top_scores = [r["score"] for r in formatted_results[:5]]
            
            if not formatted_results:
                relevance_assessment = "未找到相关文档，可能需要调整查询或降低阈值"
            elif top_scores[0] > 0.8:
                relevance_assessment = "找到高度相关的文档，检索质量优秀"
            elif top_scores[0] > 0.6:
                relevance_assessment = "找到相关文档，检索质量良好"
            elif top_scores[0] > 0.4:
                relevance_assessment = "找到部分相关文档，检索质量一般"
            else:
                relevance_assessment = "文档相关性较低，可能需要优化查询"
            
            reflection_logger.log_retrieval_evaluation(
                query=query,
                results_count=len(formatted_results),
                top_scores=top_scores,
                relevance_assessment=relevance_assessment
            )
        
        # 返回结果
        output = {
            "results": formatted_results,
            "total_count": len(formatted_results),
            "kb_id": kb_id,
            "kb_name": kb_name
        }
        
        return json.dumps(output, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"使用知识库管理器搜索失败: {e}", exc_info=True)
        error_output = {
            "error": f"知识库搜索失败: {str(e)}",
            "results": [],
            "total_count": 0,
            "kb_id": kb_id
        }
        return json.dumps(error_output, ensure_ascii=False, indent=2)


@tool
def search_knowledge_base(query: str, kb_id: Optional[str] = None) -> str:
    """
    搜索知识库获取相关信息

    此工具在 Qdrant 向量数据库中执行向量搜索，使用优化的查询。
    查询应该包含关键实体、完整上下文、解析的引用和相关同义词，以获得更好的检索结果。
    
    支持多知识库查询：
    - 如果提供 kb_id，将在指定的知识库中搜索，使用该知识库的配置
    - 如果未提供 kb_id，将使用默认知识库（向后兼容）

    参数:
        query: 优化的搜索查询，包含实体、上下文和同义词
        kb_id: 可选的知识库 ID。如果未提供，使用默认知识库

    返回:
        JSON 字符串，包含搜索结果的分数、内容、来源和元数据

    示例:
        >>> # 使用默认知识库
        >>> search_knowledge_base("李小勇合作入股投资的公司 股权结构 联合投资")
        
        >>> # 使用指定知识库
        >>> search_knowledge_base("李小勇合作入股投资的公司 股权结构 联合投资", kb_id="kb_123")
        {
            "results": [
                {
                    "score": 0.85,
                    "content": "...",
                    "source": "document.pdf",
                    "metadata": {...}
                }
            ],
            "total_count": 1,
            "kb_id": "kb_123",
            "kb_name": "financial_docs"
        }
    """
    # 记录查询开始时间和时间戳
    query_start_time = time.time()
    query_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 验证输入
    if not query or not query.strip():
        error_output = {
            "error": "查询不能为空",
            "results": [],
            "total_count": 0
        }
        logger.warning("收到空查询")
        return json.dumps(error_output, ensure_ascii=False, indent=2)

    try:
        logger.info("=" * 60)
        logger.info(f"开始搜索知识库")
        logger.info(f"时间戳: {query_timestamp}")
        logger.info(f"原始查询: {query}")
        logger.info(f"查询长度: {len(query)} 字符")
        if kb_id:
            logger.info(f"目标知识库: {kb_id}")
        else:
            logger.info("使用默认知识库（向后兼容模式）")
        logger.info("=" * 60)
        
        # 如果提供了 kb_id，使用知识库管理器进行查询
        if kb_id:
            return _search_with_kb_manager(
                query=query,
                kb_id=kb_id,
                query_start_time=query_start_time,
                query_timestamp=query_timestamp
            )

        # 获取嵌入模型管理器
        logger.info("\n[步骤 1/3] 初始化嵌入模型...")
        try:
            embeddings_manager = _get_embeddings_manager()
            logger.info(f"✓ 嵌入模型已就绪: {settings.embed_model}")
        except (ConnectionError, ValueError) as e:
            logger.error(f"✗ 嵌入模型初始化失败: {e}")
            error_output = {
                "error": f"嵌入模型初始化失败: {str(e)}",
                "results": [],
                "total_count": 0
            }
            return json.dumps(error_output, ensure_ascii=False, indent=2)

        # 获取 Qdrant 管理器
        logger.info("\n[步骤 2/3] 连接向量数据库...")
        try:
            qdrant_manager = _get_qdrant_manager()
            logger.info(f"✓ 已连接到 Qdrant: {settings.qdrant_url}")
            logger.debug(f"目标集合: {settings.collection_name}")
        except Exception as e:
            logger.error(f"✗ Qdrant 连接失败: {e}")
            error_output = {
                "error": f"Qdrant 连接失败: {str(e)}",
                "results": [],
                "total_count": 0
            }
            return json.dumps(error_output, ensure_ascii=False, indent=2)

        # 将查询转换为向量
        logger.info("\n[步骤 3/3] 向量化查询...")
        embed_start_time = time.time()
        try:
            query_vector = embeddings_manager.embed_query(query)
            embed_time = time.time() - embed_start_time
            logger.info(f"✓ 查询向量化完成")
            logger.debug(f"向量维度: {len(query_vector)}")
            logger.debug(f"向量化耗时: {embed_time:.3f}秒")
        except Exception as e:
            logger.error(f"✗ 向量化查询失败: {e}", exc_info=True)
            error_output = {
                "error": f"向量化查询失败: {str(e)}",
                "results": [],
                "total_count": 0
            }
            return json.dumps(error_output, ensure_ascii=False, indent=2)

        # 执行向量搜索
        logger.info("\n执行向量搜索...")
        logger.debug(f"搜索参数 - limit: {settings.top_k}, threshold: {settings.similarity_threshold}")
        search_start_time = time.time()
        
        try:
            search_results = qdrant_manager.search(
                collection_name=settings.collection_name,
                query_vector=query_vector,
                limit=settings.top_k,
                score_threshold=settings.similarity_threshold
            )
            search_time = time.time() - search_start_time

            logger.info(f"✓ 搜索完成，找到 {len(search_results)} 个结果")
            logger.debug(f"搜索耗时: {search_time:.3f}秒")
            
            if search_results:
                top_score = max(result.score for result in search_results)
                logger.info(f"最高相似度分数: {top_score:.4f}")
            else:
                logger.warning(
                    f"未找到相关结果 (阈值: {settings.similarity_threshold}). "
                    f"建议: 1) 降低相似度阈值, 2) 检查文档是否已索引, 3) 尝试不同的查询词"
                )
        except Exception as e:
            logger.error(f"✗ 搜索失败: {e}", exc_info=True)
            error_output = {
                "error": f"搜索失败: {str(e)}",
                "results": [],
                "total_count": 0
            }
            return json.dumps(error_output, ensure_ascii=False, indent=2)

        # 格式化结果
        logger.debug("\n格式化搜索结果...")
        formatted_results = _format_search_results(search_results)

        # 计算总耗时
        total_time = time.time() - query_start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("搜索完成")
        logger.info(f"总耗时: {total_time:.3f}秒")
        logger.info(f"返回结果数: {len(formatted_results)}")
        logger.info("=" * 60)
        
        # 记录检索评估（如果启用反思日志）
        reflection_logger = _get_reflection_logger()
        if reflection_logger:
            # 提取前几个分数
            top_scores = [result["score"] for result in formatted_results[:5]]
            
            # 评估相关性
            if not formatted_results:
                relevance_assessment = "未找到相关文档，可能需要调整查询或降低阈值"
            elif top_scores[0] > 0.8:
                relevance_assessment = "找到高度相关的文档，检索质量优秀"
            elif top_scores[0] > 0.6:
                relevance_assessment = "找到相关文档，检索质量良好"
            elif top_scores[0] > 0.4:
                relevance_assessment = "找到部分相关文档，检索质量一般"
            else:
                relevance_assessment = "文档相关性较低，可能需要优化查询"
            
            reflection_logger.log_retrieval_evaluation(
                query=query,
                results_count=len(formatted_results),
                top_scores=top_scores,
                relevance_assessment=relevance_assessment
            )

        # 返回 JSON 字符串
        output = {
            "results": formatted_results,
            "total_count": len(formatted_results)
        }

        return json.dumps(output, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"搜索知识库时发生未预期的错误: {e}", exc_info=True)
        error_output = {
            "error": f"搜索失败: {str(e)}",
            "results": [],
            "total_count": 0
        }
        return json.dumps(error_output, ensure_ascii=False, indent=2)


def get_search_tool():
    """
    获取搜索工具

    返回:
        搜索工具函数

    示例:
        >>> tool = get_search_tool()
        >>> result = tool.invoke({"query": "测试查询"})
    """
    return search_knowledge_base


def reset_managers():
    """
    重置管理器实例

    用于测试或重新初始化。

    示例:
        >>> reset_managers()
    """
    global _embeddings_manager, _qdrant_manager, _reflection_logger, _kb_manager
    _embeddings_manager = None
    _qdrant_manager = None
    _reflection_logger = None
    _kb_manager = None
    logger.info("已重置管理器实例")
