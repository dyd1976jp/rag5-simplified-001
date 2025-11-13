"""
数据摄取流程编排器

协调文档加载、分块和向量化的完整流程。
"""

import logging
import time
from pathlib import Path
from typing import List, Optional, Union
from dataclasses import dataclass

from .loaders import BaseLoader, TextLoader, PDFLoader, MarkdownLoader
from .splitters import RecursiveSplitter, ChineseTextSplitter
from .vectorizers import BatchVectorizer, VectorUploader, UploadResult
from ..utils import ChineseTextDiagnostic

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """
    摄取结果数据类

    Attributes:
        documents_loaded: 成功加载的文档数
        chunks_created: 创建的文档块数
        vectors_uploaded: 成功上传的向量数
        failed_files: 失败的文件列表
        errors: 错误信息列表
    """
    documents_loaded: int
    chunks_created: int
    vectors_uploaded: int
    failed_files: List[str]
    errors: List[str]

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total_files = self.documents_loaded + len(self.failed_files)
        if total_files == 0:
            return 0.0
        return (self.documents_loaded / total_files) * 100


class IngestionPipeline:
    """
    数据摄取流程编排器

    协调文档加载、分块和向量化的完整流程。
    支持多种文件格式，自动选择合适的加载器。
    支持中文文本自动检测和优化分块。

    Args:
        splitter: 文档分块器实例（RecursiveSplitter或ChineseTextSplitter）
        vectorizer: 批量向量化器实例
        uploader: 向量上传器实例
        loaders: 文档加载器列表。如果为None，使用默认加载器
        auto_detect_chinese: 是否自动检测中文并使用中文分块器
        chinese_threshold: 中文字符占比阈值，超过此值使用中文分块器

    示例:
        >>> from rag5.config import settings
        >>> from rag5.tools.embeddings import OllamaEmbeddingsManager
        >>> from rag5.tools.vectordb import QdrantManager
        >>>
        >>> # 初始化组件
        >>> embeddings = OllamaEmbeddingsManager(settings.embed_model, settings.ollama_host)
        >>> qdrant = QdrantManager(settings.qdrant_url)
        >>>
        >>> splitter = RecursiveSplitter(chunk_size=500, chunk_overlap=50)
        >>> vectorizer = BatchVectorizer(embeddings.embeddings, batch_size=100)
        >>> uploader = VectorUploader(qdrant, settings.collection_name)
        >>>
        >>> # 创建流程（启用中文自动检测）
        >>> pipeline = IngestionPipeline(
        ...     splitter, vectorizer, uploader,
        ...     auto_detect_chinese=True,
        ...     chinese_threshold=0.3
        ... )
        >>>
        >>> # 执行摄取
        >>> result = pipeline.ingest_directory("./docs")
        >>> print(f"成功率: {result.success_rate:.1f}%")
    """

    def __init__(
        self,
        splitter: Union[RecursiveSplitter, ChineseTextSplitter],
        vectorizer: BatchVectorizer,
        uploader: VectorUploader,
        loaders: Optional[List[BaseLoader]] = None,
        auto_detect_chinese: bool = True,
        chinese_threshold: float = 0.3
    ):
        """
        初始化摄取流程编排器

        Args:
            splitter: 文档分块器实例（RecursiveSplitter或ChineseTextSplitter）
            vectorizer: 批量向量化器实例
            uploader: 向量上传器实例
            loaders: 文档加载器列表。如果为None，使用默认加载器
            auto_detect_chinese: 是否自动检测中文并使用中文分块器
            chinese_threshold: 中文字符占比阈值，超过此值使用中文分块器
        """
        self.splitter = splitter
        self.vectorizer = vectorizer
        self.uploader = uploader
        self.auto_detect_chinese = auto_detect_chinese
        self.chinese_threshold = chinese_threshold

        # 初始化中文诊断工具
        self.chinese_diagnostic = ChineseTextDiagnostic()

        # 如果启用自动检测，准备中文分块器
        if auto_detect_chinese and isinstance(splitter, RecursiveSplitter):
            # 创建一个中文分块器作为备用
            self.chinese_splitter = ChineseTextSplitter(
                chunk_size=splitter.chunk_size,
                chunk_overlap=splitter.chunk_overlap,
                respect_sentence_boundary=True
            )
            logger.debug("启用中文自动检测，已准备ChineseTextSplitter")
        else:
            self.chinese_splitter = None

        # 使用提供的加载器或默认加载器
        if loaders is None:
            self.loaders = [
                TextLoader(),
                PDFLoader(),
                MarkdownLoader()
            ]
        else:
            self.loaders = loaders

        logger.debug(
            f"初始化IngestionPipeline，加载器数量: {len(self.loaders)}, "
            f"自动检测中文: {auto_detect_chinese}"
        )

    def _get_loader_for_file(self, file_path: str) -> Optional[BaseLoader]:
        """
        为文件选择合适的加载器

        Args:
            file_path: 文件路径

        Returns:
            支持该文件的加载器，如果没有返回None
        """
        for loader in self.loaders:
            if loader.supports(file_path):
                return loader
        return None

    def _select_splitter_for_text(self, text: str) -> Union[RecursiveSplitter, ChineseTextSplitter]:
        """
        根据文本内容选择合适的分块器

        如果启用了自动检测且文本中文占比超过阈值，使用中文分块器。

        Args:
            text: 文本内容

        Returns:
            选择的分块器实例
        """
        # 如果没有启用自动检测或没有中文分块器，使用默认分块器
        if not self.auto_detect_chinese or self.chinese_splitter is None:
            return self.splitter

        # 分析文本
        try:
            analysis = self.chinese_diagnostic.analyze_text(text)
            chinese_ratio = analysis['chinese_ratio']

            logger.debug(
                f"文本分析 - 中文占比: {chinese_ratio:.1%}, "
                f"阈值: {self.chinese_threshold:.1%}"
            )

            # 如果中文占比超过阈值，使用中文分块器
            if chinese_ratio >= self.chinese_threshold:
                logger.info(
                    f"检测到中文文本（占比: {chinese_ratio:.1%}），"
                    "使用ChineseTextSplitter"
                )
                return self.chinese_splitter
            else:
                logger.debug(
                    f"中文占比较低（{chinese_ratio:.1%}），"
                    "使用默认分块器"
                )
                return self.splitter

        except Exception as e:
            logger.warning(f"文本分析失败，使用默认分块器: {e}")
            return self.splitter

    def ingest_file(self, file_path: str) -> IngestionResult:
        """
        摄取单个文件

        Args:
            file_path: 文件路径

        Returns:
            IngestionResult对象

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持
        """
        logger.info(f"开始摄取文件: {file_path}")
        
        # 记录文件信息
        file_path_obj = Path(file_path)
        if file_path_obj.exists():
            file_size = file_path_obj.stat().st_size
            file_type = file_path_obj.suffix
            logger.info(f"文件信息 - 路径: {file_path}, 大小: {file_size} 字节, 类型: {file_type}")
        else:
            logger.error(f"文件不存在: {file_path}")
            raise FileNotFoundError(f"文件不存在: {file_path}")

        failed_files = []
        errors = []

        # 选择加载器
        loader = self._get_loader_for_file(file_path)
        if loader is None:
            error_msg = f"不支持的文件类型: {file_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.debug(f"使用加载器: {loader.__class__.__name__}")

        try:
            # 步骤1: 加载文档
            logger.info("[1/4] 加载文档...")
            start_time = time.time()
            documents = loader.load(file_path)
            load_time = time.time() - start_time
            logger.info(f"✓ 加载了 {len(documents)} 个文档 (耗时: {load_time:.2f}秒)")
            
            # 记录文档内容统计
            total_chars = sum(len(doc.page_content) for doc in documents)
            logger.debug(f"文档内容统计 - 总字符数: {total_chars}, 平均每文档: {total_chars/len(documents):.0f} 字符")

            # 步骤2: 分块
            logger.info("[2/4] 分割文档...")
            
            # 中文文本诊断（如果启用）
            if self.auto_detect_chinese and documents:
                # 合并所有文档内容进行分析
                combined_text = " ".join(doc.page_content[:1000] for doc in documents[:5])  # 采样前5个文档
                try:
                    analysis = self.chinese_diagnostic.analyze_text(combined_text)
                    logger.info(
                        f"文本诊断 - 中文占比: {analysis['chinese_ratio']:.1%}, "
                        f"字符数: {analysis['char_count']}, "
                        f"句子数: {analysis['sentence_count']}"
                    )
                    if analysis['potential_issues']:
                        logger.warning("检测到潜在问题:")
                        for issue in analysis['potential_issues']:
                            logger.warning(f"  - {issue}")
                except Exception as e:
                    logger.debug(f"文本诊断失败: {e}")
            
            # 选择合适的分块器
            selected_splitter = self._select_splitter_for_text(
                documents[0].page_content if documents else ""
            )
            
            logger.debug(
                f"分块策略 - 使用: {selected_splitter.__class__.__name__}, "
                f"chunk_size: {selected_splitter.chunk_size}, "
                f"chunk_overlap: {selected_splitter.chunk_overlap}"
            )
            
            start_time = time.time()
            chunks = selected_splitter.split_documents(documents)
            split_time = time.time() - start_time
            logger.info(f"✓ 创建了 {len(chunks)} 个块 (耗时: {split_time:.2f}秒)")
            
            # 记录分块统计
            chunk_sizes = [len(chunk.page_content) for chunk in chunks]
            avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
            min_chunk_size = min(chunk_sizes) if chunk_sizes else 0
            max_chunk_size = max(chunk_sizes) if chunk_sizes else 0
            logger.debug(
                f"分块统计 - 平均大小: {avg_chunk_size:.0f} 字符, "
                f"最小: {min_chunk_size} 字符, 最大: {max_chunk_size} 字符"
            )

            # 步骤3: 向量化
            logger.info("[3/4] 生成向量...")
            start_time = time.time()
            points = self.vectorizer.vectorize(chunks)
            vectorize_time = time.time() - start_time
            logger.info(f"✓ 生成了 {len(points)} 个向量 (耗时: {vectorize_time:.2f}秒)")
            
            # 记录向量化信息
            if points:
                vector_dim = len(points[0].vector)
                logger.debug(f"向量信息 - 维度: {vector_dim}, 数量: {len(points)}")

            # 步骤4: 上传
            logger.info("[4/4] 上传向量...")
            start_time = time.time()
            upload_result = self.uploader.upload_all(points)
            upload_time = time.time() - start_time
            logger.info(f"✓ 上传了 {upload_result.uploaded_points} 个向量 (耗时: {upload_time:.2f}秒)")
            
            # 记录上传状态
            if upload_result.uploaded_points == len(points):
                logger.debug(f"上传状态 - 成功: {upload_result.uploaded_points}/{len(points)}")
            else:
                logger.warning(
                    f"上传状态 - 部分成功: {upload_result.uploaded_points}/{len(points)}, "
                    f"失败: {len(points) - upload_result.uploaded_points}"
                )

            return IngestionResult(
                documents_loaded=1,
                chunks_created=len(chunks),
                vectors_uploaded=upload_result.uploaded_points,
                failed_files=[],
                errors=[]
            )

        except Exception as e:
            error_msg = f"摄取文件失败 {file_path}: {e}"
            logger.error(error_msg, exc_info=True)
            failed_files.append(file_path)
            errors.append(error_msg)

            return IngestionResult(
                documents_loaded=0,
                chunks_created=0,
                vectors_uploaded=0,
                failed_files=failed_files,
                errors=errors
            )

    def ingest_directory(self, directory: str) -> IngestionResult:
        """
        摄取目录中的所有支持的文件

        Args:
            directory: 目录路径

        Returns:
            IngestionResult对象，包含摄取统计信息

        Raises:
            ValueError: 目录不存在或不是目录
        """
        logger.info("=" * 60)
        logger.info("开始数据摄取流程")
        logger.info("=" * 60)

        # 验证目录
        directory_path = Path(directory)
        if not directory_path.exists():
            raise ValueError(f"目录不存在: {directory}")

        if not directory_path.is_dir():
            raise ValueError(f"路径不是目录: {directory}")

        # 收集所有支持的文件
        logger.info(f"\n扫描目录: {directory}")
        all_files = []
        supported_extensions = set()

        for loader in self.loaders:
            if hasattr(loader, 'SUPPORTED_EXTENSIONS'):
                supported_extensions.update(loader.SUPPORTED_EXTENSIONS)

        for file_path in directory_path.rglob('*'):
            if file_path.is_file():
                if file_path.suffix.lower() in supported_extensions:
                    all_files.append(file_path)

        logger.info(f"找到 {len(all_files)} 个支持的文件")
        logger.info(f"支持的格式: {', '.join(sorted(supported_extensions))}")

        if not all_files:
            logger.warning("未找到支持的文件")
            return IngestionResult(
                documents_loaded=0,
                chunks_created=0,
                vectors_uploaded=0,
                failed_files=[],
                errors=["未找到支持的文件"]
            )

        # 步骤1: 加载所有文档
        logger.info(f"\n[步骤 1/4] 加载文档...")
        all_documents = []
        failed_files = []
        errors = []
        load_start_time = time.time()

        for i, file_path in enumerate(all_files, 1):
            try:
                loader = self._get_loader_for_file(str(file_path))
                if loader is None:
                    logger.warning(f"跳过不支持的文件: {file_path.name}")
                    continue

                # 记录文件信息
                file_size = file_path.stat().st_size
                logger.info(f"  [{i}/{len(all_files)}] 加载: {file_path.name} ({file_size} 字节)")
                logger.debug(f"    使用加载器: {loader.__class__.__name__}")
                
                file_start_time = time.time()
                documents = loader.load(str(file_path))
                file_load_time = time.time() - file_start_time
                
                all_documents.extend(documents)
                
                # 记录文档内容统计
                doc_chars = sum(len(doc.page_content) for doc in documents)
                logger.info(f"    ✓ 加载了 {len(documents)} 个文档, {doc_chars} 字符 (耗时: {file_load_time:.2f}秒)")

            except Exception as e:
                error_msg = f"加载失败 {file_path.name}: {e}"
                logger.warning(f"    ✗ {error_msg}")
                logger.debug(f"    错误详情: {e}", exc_info=True)
                failed_files.append(str(file_path))
                errors.append(error_msg)
                continue
        
        load_total_time = time.time() - load_start_time

        logger.info(f"\n✓ 加载摘要:")
        logger.info(f"  - 成功: {len(all_files) - len(failed_files)}/{len(all_files)} 文件")
        logger.info(f"  - 失败: {len(failed_files)} 文件")
        logger.info(f"  - 总文档: {len(all_documents)}")
        logger.info(f"  - 总耗时: {load_total_time:.2f}秒")

        if not all_documents:
            logger.warning("未加载任何文档")
            return IngestionResult(
                documents_loaded=0,
                chunks_created=0,
                vectors_uploaded=0,
                failed_files=failed_files,
                errors=errors
            )

        # 步骤2: 分块
        logger.info(f"\n[步骤 2/4] 分割文档...")
        
        # 中文文本诊断（如果启用）
        if self.auto_detect_chinese and all_documents:
            # 合并部分文档内容进行分析
            sample_docs = all_documents[:min(10, len(all_documents))]
            combined_text = " ".join(doc.page_content[:1000] for doc in sample_docs)
            
            try:
                analysis = self.chinese_diagnostic.analyze_text(combined_text)
                logger.info(
                    f"文本诊断 - 中文占比: {analysis['chinese_ratio']:.1%}, "
                    f"总字符数: {analysis['char_count']}, "
                    f"句子数: {analysis['sentence_count']}"
                )
                
                if analysis['potential_issues']:
                    logger.warning("检测到潜在问题:")
                    for issue in analysis['potential_issues']:
                        logger.warning(f"  - {issue}")
                
                # 根据分析结果给出建议
                if analysis['chinese_ratio'] >= self.chinese_threshold:
                    logger.info(
                        f"✓ 建议: 文本中文占比较高（{analysis['chinese_ratio']:.1%}），"
                        "将使用中文优化的分块策略"
                    )
                
            except Exception as e:
                logger.debug(f"文本诊断失败: {e}")
        
        # 选择合适的分块器
        selected_splitter = self._select_splitter_for_text(
            all_documents[0].page_content if all_documents else ""
        )
        
        logger.debug(
            f"分块策略 - 使用: {selected_splitter.__class__.__name__}, "
            f"chunk_size: {selected_splitter.chunk_size}, "
            f"chunk_overlap: {selected_splitter.chunk_overlap}"
        )
        
        split_start_time = time.time()
        
        try:
            chunks = selected_splitter.split_documents(all_documents)
            split_time = time.time() - split_start_time
            
            # 记录分块统计
            chunk_sizes = [len(chunk.page_content) for chunk in chunks]
            avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
            min_chunk_size = min(chunk_sizes) if chunk_sizes else 0
            max_chunk_size = max(chunk_sizes) if chunk_sizes else 0
            
            logger.info(f"✓ 创建了 {len(chunks)} 个块 (耗时: {split_time:.2f}秒)")
            logger.debug(
                f"分块统计 - 平均: {avg_chunk_size:.0f} 字符, "
                f"最小: {min_chunk_size} 字符, 最大: {max_chunk_size} 字符"
            )
        except Exception as e:
            error_msg = f"分割文档失败: {e}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            return IngestionResult(
                documents_loaded=len(all_files) - len(failed_files),
                chunks_created=0,
                vectors_uploaded=0,
                failed_files=failed_files,
                errors=errors
            )

        # 步骤3: 向量化
        logger.info(f"\n[步骤 3/4] 生成向量...")
        vectorize_start_time = time.time()
        
        try:
            points = self.vectorizer.vectorize(chunks)
            vectorize_time = time.time() - vectorize_start_time
            
            # 记录向量化信息
            if points:
                vector_dim = len(points[0].vector)
                logger.info(f"✓ 生成了 {len(points)} 个向量 (耗时: {vectorize_time:.2f}秒)")
                logger.debug(f"向量信息 - 维度: {vector_dim}, 批次大小: {self.vectorizer.batch_size}")
                logger.debug(f"向量化速度: {len(points)/vectorize_time:.1f} 向量/秒")
            else:
                logger.warning("未生成任何向量")
        except Exception as e:
            error_msg = f"向量化失败: {e}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            return IngestionResult(
                documents_loaded=len(all_files) - len(failed_files),
                chunks_created=len(chunks),
                vectors_uploaded=0,
                failed_files=failed_files,
                errors=errors
            )

        # 步骤4: 上传
        logger.info(f"\n[步骤 4/4] 上传向量...")
        upload_start_time = time.time()
        
        try:
            upload_result = self.uploader.upload_all(points)
            upload_time = time.time() - upload_start_time
            
            # 记录上传状态
            logger.info(f"✓ 上传了 {upload_result.uploaded_points} 个向量 (耗时: {upload_time:.2f}秒)")
            
            if upload_result.uploaded_points == len(points):
                logger.debug(f"上传状态 - 成功: {upload_result.uploaded_points}/{len(points)}")
            else:
                logger.warning(
                    f"上传状态 - 部分成功: {upload_result.uploaded_points}/{len(points)}, "
                    f"失败: {len(points) - upload_result.uploaded_points}"
                )
            
            logger.debug(f"上传速度: {upload_result.uploaded_points/upload_time:.1f} 向量/秒")
        except Exception as e:
            error_msg = f"上传向量失败: {e}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            return IngestionResult(
                documents_loaded=len(all_files) - len(failed_files),
                chunks_created=len(chunks),
                vectors_uploaded=0,
                failed_files=failed_files,
                errors=errors
            )

        # 创建最终结果
        result = IngestionResult(
            documents_loaded=len(all_files) - len(failed_files),
            chunks_created=len(chunks),
            vectors_uploaded=upload_result.uploaded_points,
            failed_files=failed_files,
            errors=errors
        )

        # 输出摘要
        logger.info("\n" + "=" * 60)
        logger.info("数据摄取完成!")
        logger.info("=" * 60)
        logger.info(f"摘要:")
        logger.info(f"  - 文档加载: {result.documents_loaded}/{len(all_files)}")
        logger.info(f"  - 文档块: {result.chunks_created}")
        logger.info(f"  - 向量上传: {result.vectors_uploaded}")
        logger.info(f"  - 失败文件: {len(result.failed_files)}")
        logger.info(f"  - 成功率: {result.success_rate:.1f}%")

        if result.failed_files:
            logger.warning(f"\n失败的文件:")
            for file in result.failed_files[:10]:  # 只显示前10个
                logger.warning(f"  - {file}")
            if len(result.failed_files) > 10:
                logger.warning(f"  ... 还有 {len(result.failed_files) - 10} 个")

        return result
