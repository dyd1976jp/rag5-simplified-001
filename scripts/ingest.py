#!/usr/bin/env python3
"""
数据摄取脚本

命令行工具，用于将文档摄取到 RAG5 系统的向量数据库中。
支持批量处理目录中的文档，自动进行加载、分块和向量化。
"""

import sys
import argparse
import logging
from pathlib import Path

# 添加父目录到路径以支持导入
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag5.config import settings
from rag5.tools.embeddings import OllamaEmbeddingsManager
from rag5.tools.vectordb import QdrantManager
from rag5.ingestion.splitters import RecursiveSplitter
from rag5.ingestion.vectorizers import BatchVectorizer, VectorUploader
from rag5.ingestion.pipeline import IngestionPipeline


def setup_logging(verbose: bool = False):
    """
    配置日志系统

    参数:
        verbose: 是否启用详细日志
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def validate_directory(directory: str) -> Path:
    """
    验证目录路径

    参数:
        directory: 目录路径字符串

    返回:
        Path 对象

    异常:
        ValueError: 目录不存在或不是目录
    """
    dir_path = Path(directory)

    if not dir_path.exists():
        raise ValueError(f"目录不存在: {directory}")

    if not dir_path.is_dir():
        raise ValueError(f"路径不是目录: {directory}")

    return dir_path


def main():
    """
    主函数 - 解析命令行参数并执行数据摄取
    """
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description='RAG5 数据摄取工具 - 将文档加载到向量数据库',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 摄取 docs 目录中的所有文档
  python scripts/ingest.py docs

  # 摄取指定目录，使用详细日志
  python scripts/ingest.py /path/to/documents --verbose

  # 自定义批处理大小
  python scripts/ingest.py docs --batch-size 50

  # 打印配置信息
  python scripts/ingest.py docs --print-config

支持的文件格式:
  - 文本文件 (.txt)
  - PDF 文件 (.pdf)
  - Markdown 文件 (.md)
        """
    )

    # 必需参数
    parser.add_argument(
        'directory',
        type=str,
        help='包含要摄取文档的目录路径'
    )

    # 可选参数
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='启用详细日志输出'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=None,
        help=f'批处理大小（默认: {settings.batch_size}）'
    )

    parser.add_argument(
        '--chunk-size',
        type=int,
        default=None,
        help=f'文档分块大小（默认: {settings.chunk_size}）'
    )

    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=None,
        help=f'分块重叠大小（默认: {settings.chunk_overlap}）'
    )

    parser.add_argument(
        '--print-config',
        action='store_true',
        help='打印当前配置并退出'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='仅验证配置，不执行摄取'
    )

    # 解析参数
    args = parser.parse_args()

    # 配置日志
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # 验证配置
        logger.info("验证配置...")
        settings.validate()

        # 打印配置（如果请求）
        if args.print_config:
            settings.print_config()
            return 0

        # 仅验证模式
        if args.validate_only:
            logger.info("✓ 配置验证成功")
            return 0

        # 验证目录
        logger.info(f"验证目录: {args.directory}")
        directory = validate_directory(args.directory)
        logger.info(f"✓ 目录有效: {directory}")

        # 使用命令行参数或配置文件中的值
        batch_size = args.batch_size if args.batch_size else settings.batch_size
        chunk_size = args.chunk_size if args.chunk_size else settings.chunk_size
        chunk_overlap = args.chunk_overlap if args.chunk_overlap else settings.chunk_overlap

        logger.info("初始化组件...")

        # 初始化嵌入管理器
        logger.info(f"  - 嵌入模型: {settings.embed_model}")
        embeddings_manager = OllamaEmbeddingsManager(
            model=settings.embed_model,
            base_url=settings.ollama_host
        )

        # 检查模型可用性
        if not embeddings_manager.check_model_available():
            logger.error(f"嵌入模型 '{settings.embed_model}' 不可用")
            logger.error(f"请运行: ollama pull {settings.embed_model}")
            return 1

        # 初始化 Qdrant 管理器
        logger.info(f"  - Qdrant: {settings.qdrant_url}")
        qdrant_manager = QdrantManager(url=settings.qdrant_url)

        # 测试连接
        if not qdrant_manager.test_connection():
            logger.error("无法连接到 Qdrant")
            logger.error("请确保 Qdrant 正在运行")
            return 1

        # 确保集合存在
        logger.info(f"  - 集合: {settings.collection_name}")
        qdrant_manager.ensure_collection(
            collection_name=settings.collection_name,
            vector_dim=settings.vector_dim
        )

        # 初始化分块器
        logger.info(f"  - 分块大小: {chunk_size}, 重叠: {chunk_overlap}")
        splitter = RecursiveSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=settings.separators
        )

        # 初始化向量化器
        logger.info(f"  - 批处理大小: {batch_size}")
        vectorizer = BatchVectorizer(
            embeddings=embeddings_manager.embeddings,
            batch_size=batch_size
        )

        # 初始化上传器
        uploader = VectorUploader(
            qdrant_manager=qdrant_manager,
            collection_name=settings.collection_name
        )

        # 创建摄取流程
        logger.info("✓ 组件初始化完成")
        pipeline = IngestionPipeline(
            splitter=splitter,
            vectorizer=vectorizer,
            uploader=uploader
        )

        # 执行摄取
        logger.info("")
        result = pipeline.ingest_directory(str(directory))

        # 检查结果
        if result.errors:
            logger.warning(f"\n摄取完成，但有 {len(result.errors)} 个错误")
            return 1

        logger.info("\n✓ 摄取成功完成")
        return 0

    except ValueError as e:
        logger.error(f"配置错误: {e}")
        return 1
    except ConnectionError as e:
        logger.error(f"连接错误: {e}")
        return 1
    except KeyboardInterrupt:
        logger.warning("\n用户中断操作")
        return 130
    except Exception as e:
        logger.error(f"摄取失败: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
