"""
索引管理器模块

提供索引管理功能，包括清空集合、重新索引目录和验证索引结果。
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from rag5.tools.vectordb import QdrantManager
from rag5.ingestion.pipeline import IngestionPipeline, IngestionResult

logger = logging.getLogger(__name__)


@dataclass
class IndexReport:
    """
    索引报告数据类

    Attributes:
        success: 是否成功
        documents_indexed: 成功索引的文档数
        chunks_created: 创建的文档块数
        vectors_uploaded: 成功上传的向量数
        failed_files: 失败的文件列表
        errors: 错误信息列表
        total_time: 总耗时（秒）
        timestamp: 时间戳
    """
    success: bool
    documents_indexed: int
    chunks_created: int
    vectors_uploaded: int
    failed_files: List[str]
    errors: List[str]
    total_time: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'documents_indexed': self.documents_indexed,
            'chunks_created': self.chunks_created,
            'vectors_uploaded': self.vectors_uploaded,
            'failed_files': self.failed_files,
            'errors': self.errors,
            'total_time': self.total_time,
            'timestamp': self.timestamp.isoformat()
        }


class IndexManager:
    """
    索引管理器

    提供索引管理功能，包括清空集合、重新索引目录和验证索引结果。
    支持增量索引（仅索引新增或修改的文档）。

    Args:
        qdrant_manager: Qdrant管理器实例
        ingestion_pipeline: 摄取流程实例

    示例:
        >>> from rag5.config import settings
        >>> from rag5.tools.vectordb import QdrantManager
        >>> from rag5.tools.embeddings import OllamaEmbeddingsManager
        >>> from rag5.ingestion import IngestionPipeline, RecursiveSplitter, BatchVectorizer, VectorUploader
        >>>
        >>> # 初始化组件
        >>> qdrant = QdrantManager(settings.qdrant_url)
        >>> embeddings = OllamaEmbeddingsManager(settings.embed_model, settings.ollama_host)
        >>> splitter = RecursiveSplitter(chunk_size=500, chunk_overlap=50)
        >>> vectorizer = BatchVectorizer(embeddings.embeddings, batch_size=100)
        >>> uploader = VectorUploader(qdrant, settings.collection_name)
        >>> pipeline = IngestionPipeline(splitter, vectorizer, uploader)
        >>>
        >>> # 创建索引管理器
        >>> manager = IndexManager(qdrant, pipeline)
        >>>
        >>> # 清空集合
        >>> manager.clear_collection("knowledge_base")
        >>>
        >>> # 重新索引
        >>> report = manager.reindex_directory("./docs", "knowledge_base", force=True)
        >>> print(f"成功索引 {report.documents_indexed} 个文档")
    """

    def __init__(
        self,
        qdrant_manager: QdrantManager,
        ingestion_pipeline: IngestionPipeline
    ):
        """
        初始化索引管理器

        Args:
            qdrant_manager: Qdrant管理器实例
            ingestion_pipeline: 摄取流程实例
        """
        self.qdrant_manager = qdrant_manager
        self.ingestion_pipeline = ingestion_pipeline
        
        # 用于增量索引的文件跟踪
        self._indexed_files: Dict[str, float] = {}  # {file_path: modification_time}
        
        logger.debug("初始化IndexManager")

    def clear_collection(self, collection_name: str) -> bool:
        """
        清空集合

        删除指定的集合及其所有数据。

        Args:
            collection_name: 集合名称

        Returns:
            是否成功清空

        示例:
            >>> manager = IndexManager(qdrant, pipeline)
            >>> if manager.clear_collection("knowledge_base"):
            ...     print("集合已清空")
        """
        logger.info(f"清空集合: {collection_name}")
        
        try:
            # 检查集合是否存在
            if not self.qdrant_manager.collection_exists(collection_name):
                logger.warning(f"集合 '{collection_name}' 不存在，无需清空")
                return True
            
            # 获取集合信息
            info = self.qdrant_manager.get_collection_info(collection_name)
            if info:
                logger.info(
                    f"集合信息 - 点数量: {info['points_count']}, "
                    f"向量数量: {info['vectors_count']}"
                )
            
            # 删除集合
            success = self.qdrant_manager.delete_collection(collection_name)
            
            if success:
                logger.info(f"✓ 集合 '{collection_name}' 已清空")
                # 清空文件跟踪
                self._indexed_files.clear()
            else:
                logger.error(f"✗ 清空集合 '{collection_name}' 失败")
            
            return success
            
        except Exception as e:
            logger.error(f"清空集合时出错: {e}", exc_info=True)
            return False

    def reindex_directory(
        self,
        directory: str,
        collection_name: str,
        force: bool = False,
        vector_dim: int = 1024
    ) -> IndexReport:
        """
        重新索引目录

        索引指定目录下的所有支持的文档。
        如果force=True，会先清空现有集合。
        如果force=False，执行增量索引（仅索引新增或修改的文档）。

        Args:
            directory: 文档目录路径
            collection_name: 集合名称
            force: 是否强制重新索引（清空现有数据）
            vector_dim: 向量维度

        Returns:
            IndexReport对象，包含索引统计信息

        Raises:
            ValueError: 目录不存在或不是目录

        示例:
            >>> manager = IndexManager(qdrant, pipeline)
            >>>
            >>> # 强制重新索引
            >>> report = manager.reindex_directory(
            ...     "./docs",
            ...     "knowledge_base",
            ...     force=True
            ... )
            >>> print(f"索引报告:")
            >>> print(f"  - 成功: {report.success}")
            >>> print(f"  - 文档数: {report.documents_indexed}")
            >>> print(f"  - 向量数: {report.vectors_uploaded}")
            >>> print(f"  - 耗时: {report.total_time:.2f}秒")
        """
        logger.info("=" * 60)
        logger.info("开始重新索引流程")
        logger.info("=" * 60)
        logger.info(f"目录: {directory}")
        logger.info(f"集合: {collection_name}")
        logger.info(f"强制重新索引: {force}")
        
        start_time = time.time()
        
        try:
            # 验证目录
            directory_path = Path(directory)
            if not directory_path.exists():
                raise ValueError(f"目录不存在: {directory}")
            if not directory_path.is_dir():
                raise ValueError(f"路径不是目录: {directory}")
            
            # 如果强制重新索引，清空集合
            if force:
                logger.info("\n[步骤 1/3] 清空现有集合...")
                self.clear_collection(collection_name)
            else:
                logger.info("\n[步骤 1/3] 增量索引模式，保留现有数据...")
                # 加载已索引文件列表
                self._load_indexed_files(directory)
            
            # 确保集合存在
            logger.info(f"\n[步骤 2/3] 确保集合存在...")
            self.qdrant_manager.ensure_collection(
                collection_name=collection_name,
                vector_dim=vector_dim
            )
            logger.info(f"✓ 集合 '{collection_name}' 已准备就绪")
            
            # 执行摄取
            logger.info(f"\n[步骤 3/3] 执行文档摄取...")
            
            if force:
                # 全量索引
                result = self.ingestion_pipeline.ingest_directory(directory)
            else:
                # 增量索引：只处理新增或修改的文件
                result = self._incremental_ingest(directory)
            
            # 计算总耗时
            total_time = time.time() - start_time
            
            # 创建索引报告
            report = IndexReport(
                success=len(result.errors) == 0,
                documents_indexed=result.documents_loaded,
                chunks_created=result.chunks_created,
                vectors_uploaded=result.vectors_uploaded,
                failed_files=result.failed_files,
                errors=result.errors,
                total_time=total_time,
                timestamp=datetime.now()
            )
            
            # 输出报告
            self._print_report(report)
            
            return report
            
        except Exception as e:
            error_msg = f"重新索引失败: {e}"
            logger.error(error_msg, exc_info=True)
            
            total_time = time.time() - start_time
            
            return IndexReport(
                success=False,
                documents_indexed=0,
                chunks_created=0,
                vectors_uploaded=0,
                failed_files=[],
                errors=[error_msg],
                total_time=total_time,
                timestamp=datetime.now()
            )

    def verify_indexing(
        self,
        collection_name: str,
        test_queries: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        验证索引结果

        检查集合状态并可选地执行测试查询。

        Args:
            collection_name: 集合名称
            test_queries: 测试查询列表（可选）

        Returns:
            验证结果字典，包含集合统计和测试结果

        示例:
            >>> manager = IndexManager(qdrant, pipeline)
            >>> result = manager.verify_indexing(
            ...     "knowledge_base",
            ...     test_queries=["于朦朧", "测试查询"]
            ... )
            >>> print(f"集合点数: {result['collection_stats']['points_count']}")
            >>> for test in result['test_results']:
            ...     print(f"查询 '{test['query']}': {test['results_count']} 个结果")
        """
        logger.info("=" * 60)
        logger.info("验证索引结果")
        logger.info("=" * 60)
        logger.info(f"集合: {collection_name}")
        
        result = {
            'collection_stats': {},
            'test_results': []
        }
        
        try:
            # 检查集合是否存在
            if not self.qdrant_manager.collection_exists(collection_name):
                logger.error(f"✗ 集合 '{collection_name}' 不存在")
                result['error'] = f"集合 '{collection_name}' 不存在"
                return result
            
            # 获取集合统计信息
            logger.info("\n[1/2] 获取集合统计信息...")
            info = self.qdrant_manager.get_collection_info(collection_name)
            
            if info:
                result['collection_stats'] = info
                logger.info(f"✓ 集合统计:")
                logger.info(f"  - 点数量: {info['points_count']}")
                logger.info(f"  - 向量数量: {info['vectors_count']}")
                logger.info(f"  - 状态: {info['status']}")
            else:
                logger.warning("无法获取集合信息")
            
            # 执行测试查询
            if test_queries:
                logger.info(f"\n[2/2] 执行测试查询 ({len(test_queries)} 个)...")
                
                from rag5.tools.embeddings import OllamaEmbeddingsManager
                from rag5.config import settings
                
                # 初始化嵌入管理器
                embeddings = OllamaEmbeddingsManager(
                    settings.embed_model,
                    settings.ollama_host
                )
                
                for i, query in enumerate(test_queries, 1):
                    logger.info(f"\n  测试查询 {i}/{len(test_queries)}: '{query}'")
                    
                    try:
                        # 向量化查询
                        query_vector = embeddings.embed_query(query)
                        
                        # 执行搜索
                        search_results = self.qdrant_manager.search(
                            collection_name=collection_name,
                            query_vector=query_vector,
                            limit=5,
                            score_threshold=0.3
                        )
                        
                        test_result = {
                            'query': query,
                            'results_count': len(search_results),
                            'top_scores': [r.score for r in search_results[:3]]
                        }
                        
                        result['test_results'].append(test_result)
                        
                        logger.info(f"    ✓ 找到 {len(search_results)} 个结果")
                        if search_results:
                            logger.info(f"    最高分数: {search_results[0].score:.4f}")
                        
                    except Exception as e:
                        logger.error(f"    ✗ 查询失败: {e}")
                        result['test_results'].append({
                            'query': query,
                            'error': str(e)
                        })
            
            logger.info("\n" + "=" * 60)
            logger.info("验证完成")
            logger.info("=" * 60)
            
            return result
            
        except Exception as e:
            logger.error(f"验证索引时出错: {e}", exc_info=True)
            result['error'] = str(e)
            return result

    def _load_indexed_files(self, directory: str) -> None:
        """
        加载已索引文件列表

        扫描目录并记录所有文件的修改时间。

        Args:
            directory: 目录路径
        """
        logger.debug(f"加载已索引文件列表: {directory}")
        
        directory_path = Path(directory)
        self._indexed_files.clear()
        
        for file_path in directory_path.rglob('*'):
            if file_path.is_file():
                try:
                    mtime = file_path.stat().st_mtime
                    self._indexed_files[str(file_path)] = mtime
                except Exception as e:
                    logger.debug(f"无法获取文件修改时间 {file_path}: {e}")
        
        logger.debug(f"已记录 {len(self._indexed_files)} 个文件")

    def _incremental_ingest(self, directory: str) -> IngestionResult:
        """
        执行增量摄取

        只处理新增或修改的文件。

        Args:
            directory: 目录路径

        Returns:
            IngestionResult对象
        """
        logger.info("执行增量索引...")
        
        directory_path = Path(directory)
        new_or_modified_files = []
        
        # 查找新增或修改的文件
        for file_path in directory_path.rglob('*'):
            if file_path.is_file():
                file_str = str(file_path)
                
                try:
                    current_mtime = file_path.stat().st_mtime
                    
                    # 检查是否是新文件或已修改
                    if file_str not in self._indexed_files:
                        logger.debug(f"新文件: {file_path.name}")
                        new_or_modified_files.append(file_path)
                    elif current_mtime > self._indexed_files[file_str]:
                        logger.debug(f"已修改文件: {file_path.name}")
                        new_or_modified_files.append(file_path)
                    
                except Exception as e:
                    logger.debug(f"检查文件时出错 {file_path}: {e}")
        
        if not new_or_modified_files:
            logger.info("没有新增或修改的文件，跳过索引")
            return IngestionResult(
                documents_loaded=0,
                chunks_created=0,
                vectors_uploaded=0,
                failed_files=[],
                errors=[]
            )
        
        logger.info(f"找到 {len(new_or_modified_files)} 个新增或修改的文件")
        
        # 处理这些文件
        all_results = []
        for file_path in new_or_modified_files:
            try:
                result = self.ingestion_pipeline.ingest_file(str(file_path))
                all_results.append(result)
                
                # 更新文件跟踪
                self._indexed_files[str(file_path)] = file_path.stat().st_mtime
                
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")
                all_results.append(IngestionResult(
                    documents_loaded=0,
                    chunks_created=0,
                    vectors_uploaded=0,
                    failed_files=[str(file_path)],
                    errors=[str(e)]
                ))
        
        # 合并结果
        total_docs = sum(r.documents_loaded for r in all_results)
        total_chunks = sum(r.chunks_created for r in all_results)
        total_vectors = sum(r.vectors_uploaded for r in all_results)
        all_failed = []
        all_errors = []
        
        for r in all_results:
            all_failed.extend(r.failed_files)
            all_errors.extend(r.errors)
        
        return IngestionResult(
            documents_loaded=total_docs,
            chunks_created=total_chunks,
            vectors_uploaded=total_vectors,
            failed_files=all_failed,
            errors=all_errors
        )

    def _print_report(self, report: IndexReport) -> None:
        """
        打印索引报告

        Args:
            report: IndexReport对象
        """
        logger.info("\n" + "=" * 60)
        logger.info("索引报告")
        logger.info("=" * 60)
        logger.info(f"状态: {'✓ 成功' if report.success else '✗ 失败'}")
        logger.info(f"时间戳: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"总耗时: {report.total_time:.2f}秒")
        logger.info("")
        logger.info("统计信息:")
        logger.info(f"  - 文档索引: {report.documents_indexed}")
        logger.info(f"  - 文档块: {report.chunks_created}")
        logger.info(f"  - 向量上传: {report.vectors_uploaded}")
        logger.info(f"  - 失败文件: {len(report.failed_files)}")
        
        if report.failed_files:
            logger.warning("\n失败的文件:")
            for file in report.failed_files[:10]:
                logger.warning(f"  - {file}")
            if len(report.failed_files) > 10:
                logger.warning(f"  ... 还有 {len(report.failed_files) - 10} 个")
        
        if report.errors:
            logger.error("\n错误信息:")
            for error in report.errors[:5]:
                logger.error(f"  - {error}")
            if len(report.errors) > 5:
                logger.error(f"  ... 还有 {len(report.errors) - 5} 个")
        
        logger.info("=" * 60)
