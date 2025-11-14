#!/usr/bin/env python3
"""
索引管理命令行工具

提供命令行接口用于管理向量数据库索引。

支持的命令:
- clear: 清空集合
- reindex: 重新索引目录
- verify: 验证索引结果

使用示例:
    # 清空集合
    python -m rag5.tools.index_manager.cli clear --collection knowledge_base

    # 重新索引（强制）
    python -m rag5.tools.index_manager.cli reindex --directory ./docs --collection knowledge_base --force

    # 增量索引
    python -m rag5.tools.index_manager.cli reindex --directory ./docs --collection knowledge_base

    # 验证索引
    python -m rag5.tools.index_manager.cli verify --collection knowledge_base --test-query "于朦朧"
"""

import argparse
import sys
import logging
from pathlib import Path

from rag5.config import settings
from rag5.utils.logging_config import RAGLogger
from rag5.tools.vectordb import QdrantManager
from rag5.tools.embeddings import OllamaEmbeddingsManager
from rag5.ingestion import (
    IngestionPipeline,
    RecursiveSplitter,
    BatchVectorizer,
    VectorUploader
)
from rag5.tools.index_manager import IndexManager

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """
    设置日志

    Args:
        verbose: 是否启用详细日志
    """
    log_level = "DEBUG" if verbose else "INFO"
    RAGLogger.setup_logging(
        log_level=log_level,
        log_file="logs/index_manager.log",
        enable_console=True
    )


def create_index_manager() -> IndexManager:
    """
    创建索引管理器实例

    Returns:
        IndexManager实例
    """
    # 初始化组件
    qdrant = QdrantManager(settings.qdrant_url)
    embeddings = OllamaEmbeddingsManager(settings.embed_model, settings.ollama_host)
    
    # 创建摄取流程
    splitter = RecursiveSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )
    vectorizer = BatchVectorizer(
        embeddings.embeddings,
        batch_size=settings.batch_size
    )
    uploader = VectorUploader(qdrant, settings.collection_name)
    
    pipeline = IngestionPipeline(
        splitter,
        vectorizer,
        uploader,
        auto_detect_chinese=True,
        chinese_threshold=0.3
    )
    
    return IndexManager(qdrant, pipeline)


def cmd_clear(args):
    """
    清空集合命令

    Args:
        args: 命令行参数
    """
    logger.info("执行清空集合命令")
    
    try:
        manager = create_index_manager()
        
        # 确认操作
        if not args.yes:
            response = input(
                f"确定要清空集合 '{args.collection}' 吗？"
                "这将删除所有数据。(y/N): "
            )
            if response.lower() != 'y':
                logger.info("操作已取消")
                return 0
        
        # 执行清空
        success = manager.clear_collection(args.collection)
        
        if success:
            logger.info("✓ 集合清空成功")
            return 0
        else:
            logger.error("✗ 集合清空失败")
            return 1
            
    except Exception as e:
        logger.error(f"清空集合时出错: {e}", exc_info=True)
        return 1


def cmd_reindex(args):
    """
    重新索引命令

    Args:
        args: 命令行参数
    """
    logger.info("执行重新索引命令")
    
    try:
        # 验证目录
        directory = Path(args.directory)
        if not directory.exists():
            logger.error(f"目录不存在: {args.directory}")
            return 1
        if not directory.is_dir():
            logger.error(f"路径不是目录: {args.directory}")
            return 1
        
        manager = create_index_manager()
        
        # 确认强制重新索引
        if args.force and not args.yes:
            response = input(
                f"确定要强制重新索引集合 '{args.collection}' 吗？"
                "这将删除所有现有数据。(y/N): "
            )
            if response.lower() != 'y':
                logger.info("操作已取消")
                return 0
        
        # 执行重新索引
        report = manager.reindex_directory(
            directory=args.directory,
            collection_name=args.collection,
            force=args.force,
            vector_dim=args.vector_dim
        )
        
        # 输出报告
        print("\n" + "=" * 60)
        print("索引报告")
        print("=" * 60)
        print(f"状态: {'✓ 成功' if report.success else '✗ 失败'}")
        print(f"时间戳: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {report.total_time:.2f}秒")
        print("")
        print("统计信息:")
        print(f"  - 文档索引: {report.documents_indexed}")
        print(f"  - 文档块: {report.chunks_created}")
        print(f"  - 向量上传: {report.vectors_uploaded}")
        print(f"  - 失败文件: {len(report.failed_files)}")
        
        if report.failed_files:
            print("\n失败的文件:")
            for file in report.failed_files[:10]:
                print(f"  - {file}")
            if len(report.failed_files) > 10:
                print(f"  ... 还有 {len(report.failed_files) - 10} 个")
        
        print("=" * 60)
        
        return 0 if report.success else 1
        
    except Exception as e:
        logger.error(f"重新索引时出错: {e}", exc_info=True)
        return 1


def cmd_verify(args):
    """
    验证索引命令

    Args:
        args: 命令行参数
    """
    logger.info("执行验证索引命令")
    
    try:
        manager = create_index_manager()
        
        # 准备测试查询
        test_queries = []
        if args.test_query:
            if isinstance(args.test_query, list):
                test_queries = args.test_query
            else:
                test_queries = [args.test_query]
        
        # 执行验证
        result = manager.verify_indexing(
            collection_name=args.collection,
            test_queries=test_queries if test_queries else None
        )
        
        # 输出结果
        print("\n" + "=" * 60)
        print("验证结果")
        print("=" * 60)
        
        if 'error' in result:
            print(f"✗ 错误: {result['error']}")
            return 1
        
        # 集合统计
        if result['collection_stats']:
            stats = result['collection_stats']
            print("\n集合统计:")
            print(f"  - 点数量: {stats.get('points_count', 0)}")
            print(f"  - 向量数量: {stats.get('vectors_count', 0)}")
            print(f"  - 状态: {stats.get('status', 'unknown')}")
        
        # 测试结果
        if result['test_results']:
            print("\n测试查询结果:")
            for i, test in enumerate(result['test_results'], 1):
                print(f"\n  [{i}] 查询: '{test['query']}'")
                if 'error' in test:
                    print(f"      ✗ 错误: {test['error']}")
                else:
                    print(f"      ✓ 结果数: {test['results_count']}")
                    if test['top_scores']:
                        print(f"      最高分数: {test['top_scores']}")
        
        print("\n" + "=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"验证索引时出错: {e}", exc_info=True)
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="索引管理命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 清空集合
  %(prog)s clear --collection knowledge_base

  # 重新索引（强制）
  %(prog)s reindex --directory ./docs --collection knowledge_base --force

  # 增量索引
  %(prog)s reindex --directory ./docs --collection knowledge_base

  # 验证索引
  %(prog)s verify --collection knowledge_base --test-query "于朦朧"
        """
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='启用详细日志'
    )
    
    subparsers = parser.add_subparsers(
        dest='command',
        help='可用命令'
    )
    
    # clear 命令
    clear_parser = subparsers.add_parser(
        'clear',
        help='清空集合'
    )
    clear_parser.add_argument(
        '--collection',
        default=settings.collection_name,
        help=f'集合名称 (默认: {settings.collection_name})'
    )
    clear_parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='跳过确认提示'
    )
    
    # reindex 命令
    reindex_parser = subparsers.add_parser(
        'reindex',
        help='重新索引目录'
    )
    reindex_parser.add_argument(
        '--directory',
        required=True,
        help='文档目录路径'
    )
    reindex_parser.add_argument(
        '--collection',
        default=settings.collection_name,
        help=f'集合名称 (默认: {settings.collection_name})'
    )
    reindex_parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新索引（清空现有数据）'
    )
    reindex_parser.add_argument(
        '--vector-dim',
        type=int,
        default=settings.vector_dim,
        help=f'向量维度 (默认: {settings.vector_dim})'
    )
    reindex_parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='跳过确认提示'
    )
    
    # verify 命令
    verify_parser = subparsers.add_parser(
        'verify',
        help='验证索引结果'
    )
    verify_parser.add_argument(
        '--collection',
        default=settings.collection_name,
        help=f'集合名称 (默认: {settings.collection_name})'
    )
    verify_parser.add_argument(
        '--test-query',
        action='append',
        help='测试查询（可多次指定）'
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    
    # 如果没有指定命令，显示帮助
    if not args.command:
        parser.print_help()
        return 1
    
    # 执行命令
    try:
        if args.command == 'clear':
            return cmd_clear(args)
        elif args.command == 'reindex':
            return cmd_reindex(args)
        elif args.command == 'verify':
            return cmd_verify(args)
        else:
            logger.error(f"未知命令: {args.command}")
            return 1
    except KeyboardInterrupt:
        logger.info("\n操作已取消")
        return 130
    except Exception as e:
        logger.error(f"执行命令时出错: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
