#!/usr/bin/env python3
"""
知识库管理 CLI 工具

命令行工具，用于管理 RAG5 系统的知识库。
支持创建、列出、更新、删除知识库，以及文件上传和查询功能。
"""

import sys
import argparse
import asyncio
import logging
import json
from pathlib import Path
from typing import Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag5.config import settings
from rag5.core.knowledge_base import (
    KnowledgeBaseManager,
    ChunkConfig,
    RetrievalConfig,
    FileStatus,
    KnowledgeBaseError,
    KnowledgeBaseNotFoundError,
    KnowledgeBaseAlreadyExistsError,
    FileValidationError
)
from rag5.tools.vectordb import QdrantManager


def setup_logging(verbose: bool = False):
    """配置日志系统"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def get_manager() -> KnowledgeBaseManager:
    """
    创建并初始化知识库管理器
    
    返回:
        初始化后的 KnowledgeBaseManager 实例
    """
    # 获取数据库路径
    db_path = getattr(settings, 'kb_database_path', './data/knowledge_bases.db')
    
    # 确保数据目录存在
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 初始化 Qdrant 管理器
    qdrant_manager = QdrantManager(url=settings.qdrant_url)
    
    # 创建知识库管理器
    manager = KnowledgeBaseManager(
        db_path=db_path,
        qdrant_manager=qdrant_manager,
        file_storage_path=getattr(settings, 'file_storage_path', './docs'),
        embedding_dimension=settings.vector_dim
    )
    
    return manager


# ==================== 命令处理函数 ====================

async def cmd_create(args):
    """创建知识库"""
    logger = logging.getLogger(__name__)
    
    try:
        manager = get_manager()
        await manager.initialize()
        
        # 解析分块配置
        chunk_config = None
        if any([args.chunk_size, args.chunk_overlap, args.parser_type]):
            chunk_config = ChunkConfig(
                chunk_size=args.chunk_size or 512,
                chunk_overlap=args.chunk_overlap or 50,
                parser_type=args.parser_type or "sentence"
            )
        
        # 解析检索配置
        retrieval_config = None
        if any([args.top_k, args.similarity_threshold, args.retrieval_mode]):
            retrieval_config = RetrievalConfig(
                top_k=args.top_k or 5,
                similarity_threshold=args.similarity_threshold or 0.3,
                retrieval_mode=args.retrieval_mode or "hybrid"
            )
        
        # 创建知识库
        kb = await manager.create_knowledge_base(
            name=args.name,
            description=args.description or "",
            embedding_model=args.embedding_model,
            chunk_config=chunk_config,
            retrieval_config=retrieval_config
        )
        
        print(f"\n✓ 知识库创建成功!")
        print(f"  ID: {kb.id}")
        print(f"  名称: {kb.name}")
        print(f"  描述: {kb.description}")
        print(f"  嵌入模型: {kb.embedding_model}")
        print(f"  创建时间: {kb.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if args.json:
            print(f"\nJSON 输出:")
            print(json.dumps({
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "embedding_model": kb.embedding_model,
                "created_at": kb.created_at.isoformat()
            }, indent=2, ensure_ascii=False))
        
        return 0
        
    except KnowledgeBaseAlreadyExistsError as e:
        logger.error(f"✗ {e}")
        return 1
    except Exception as e:
        logger.error(f"✗ 创建知识库失败: {e}", exc_info=args.verbose)
        return 1


async def cmd_list(args):
    """列出知识库"""
    logger = logging.getLogger(__name__)
    
    try:
        manager = get_manager()
        await manager.initialize()
        
        # 列出知识库
        kbs, total = await manager.list_knowledge_bases(
            page=args.page,
            size=args.size
        )
        
        if not kbs:
            print("\n未找到知识库")
            return 0
        
        print(f"\n知识库列表 (共 {total} 个，当前第 {args.page} 页):")
        print("=" * 80)
        
        for kb in kbs:
            print(f"\nID: {kb.id}")
            print(f"名称: {kb.name}")
            print(f"描述: {kb.description}")
            print(f"嵌入模型: {kb.embedding_model}")
            print(f"文档数: {kb.document_count}")
            print(f"总大小: {kb.total_size:,} 字节")
            print(f"创建时间: {kb.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 80)
        
        # 分页信息
        total_pages = (total + args.size - 1) // args.size
        print(f"\n第 {args.page}/{total_pages} 页")
        
        if args.json:
            print(f"\nJSON 输出:")
            print(json.dumps({
                "total": total,
                "page": args.page,
                "size": args.size,
                "knowledge_bases": [
                    {
                        "id": kb.id,
                        "name": kb.name,
                        "description": kb.description,
                        "embedding_model": kb.embedding_model,
                        "document_count": kb.document_count,
                        "total_size": kb.total_size,
                        "created_at": kb.created_at.isoformat()
                    }
                    for kb in kbs
                ]
            }, indent=2, ensure_ascii=False))
        
        return 0
        
    except Exception as e:
        logger.error(f"✗ 列出知识库失败: {e}", exc_info=args.verbose)
        return 1


async def cmd_get(args):
    """获取知识库详情"""
    logger = logging.getLogger(__name__)
    
    try:
        manager = get_manager()
        await manager.initialize()
        
        # 获取知识库
        kb = await manager.get_knowledge_base(args.kb_id)
        
        print(f"\n知识库详情:")
        print("=" * 80)
        print(f"ID: {kb.id}")
        print(f"名称: {kb.name}")
        print(f"描述: {kb.description}")
        print(f"嵌入模型: {kb.embedding_model}")
        print(f"\n分块配置:")
        print(f"  块大小: {kb.chunk_config.chunk_size}")
        print(f"  重叠大小: {kb.chunk_config.chunk_overlap}")
        print(f"  解析器类型: {kb.chunk_config.parser_type}")
        print(f"\n检索配置:")
        print(f"  检索模式: {kb.retrieval_config.retrieval_mode}")
        print(f"  Top K: {kb.retrieval_config.top_k}")
        print(f"  相似度阈值: {kb.retrieval_config.similarity_threshold}")
        print(f"  向量权重: {kb.retrieval_config.vector_weight}")
        print(f"  启用重排序: {kb.retrieval_config.enable_rerank}")
        print(f"\n统计信息:")
        print(f"  文档数: {kb.document_count}")
        print(f"  总大小: {kb.total_size:,} 字节")
        print(f"\n时间信息:")
        print(f"  创建时间: {kb.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  更新时间: {kb.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if args.json:
            print(f"\nJSON 输出:")
            print(json.dumps({
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "embedding_model": kb.embedding_model,
                "chunk_config": {
                    "chunk_size": kb.chunk_config.chunk_size,
                    "chunk_overlap": kb.chunk_config.chunk_overlap,
                    "parser_type": kb.chunk_config.parser_type
                },
                "retrieval_config": {
                    "retrieval_mode": kb.retrieval_config.retrieval_mode,
                    "top_k": kb.retrieval_config.top_k,
                    "similarity_threshold": kb.retrieval_config.similarity_threshold,
                    "vector_weight": kb.retrieval_config.vector_weight,
                    "enable_rerank": kb.retrieval_config.enable_rerank
                },
                "document_count": kb.document_count,
                "total_size": kb.total_size,
                "created_at": kb.created_at.isoformat(),
                "updated_at": kb.updated_at.isoformat()
            }, indent=2, ensure_ascii=False))
        
        return 0
        
    except KnowledgeBaseNotFoundError as e:
        logger.error(f"✗ {e}")
        return 1
    except Exception as e:
        logger.error(f"✗ 获取知识库失败: {e}", exc_info=args.verbose)
        return 1


async def cmd_update(args):
    """更新知识库"""
    logger = logging.getLogger(__name__)
    
    try:
        manager = get_manager()
        await manager.initialize()
        
        # 构建更新字典
        updates = {}
        
        if args.name:
            updates["name"] = args.name
        if args.description is not None:
            updates["description"] = args.description
        if args.embedding_model:
            updates["embedding_model"] = args.embedding_model
        
        # 更新分块配置
        if any([args.chunk_size, args.chunk_overlap, args.parser_type]):
            # 获取当前配置
            kb = await manager.get_knowledge_base(args.kb_id)
            chunk_config = ChunkConfig(
                chunk_size=args.chunk_size or kb.chunk_config.chunk_size,
                chunk_overlap=args.chunk_overlap or kb.chunk_config.chunk_overlap,
                parser_type=args.parser_type or kb.chunk_config.parser_type
            )
            updates["chunk_config"] = chunk_config
        
        # 更新检索配置
        if any([args.top_k, args.similarity_threshold, args.retrieval_mode]):
            # 获取当前配置
            kb = await manager.get_knowledge_base(args.kb_id)
            retrieval_config = RetrievalConfig(
                top_k=args.top_k or kb.retrieval_config.top_k,
                similarity_threshold=args.similarity_threshold or kb.retrieval_config.similarity_threshold,
                retrieval_mode=args.retrieval_mode or kb.retrieval_config.retrieval_mode,
                vector_weight=kb.retrieval_config.vector_weight,
                enable_rerank=kb.retrieval_config.enable_rerank,
                rerank_model=kb.retrieval_config.rerank_model
            )
            updates["retrieval_config"] = retrieval_config
        
        if not updates:
            logger.error("✗ 未指定任何更新字段")
            return 1
        
        # 更新知识库
        kb = await manager.update_knowledge_base(args.kb_id, **updates)
        
        print(f"\n✓ 知识库更新成功!")
        print(f"  ID: {kb.id}")
        print(f"  名称: {kb.name}")
        print(f"  更新时间: {kb.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if args.json:
            print(f"\nJSON 输出:")
            print(json.dumps({
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "updated_at": kb.updated_at.isoformat()
            }, indent=2, ensure_ascii=False))
        
        return 0
        
    except (KnowledgeBaseNotFoundError, KnowledgeBaseAlreadyExistsError) as e:
        logger.error(f"✗ {e}")
        return 1
    except Exception as e:
        logger.error(f"✗ 更新知识库失败: {e}", exc_info=args.verbose)
        return 1


async def cmd_delete(args):
    """删除知识库"""
    logger = logging.getLogger(__name__)
    
    try:
        manager = get_manager()
        await manager.initialize()
        
        # 获取知识库信息
        kb = await manager.get_knowledge_base(args.kb_id)
        
        # 确认删除
        if not args.yes:
            print(f"\n警告: 即将删除知识库 '{kb.name}' (ID: {kb.id})")
            print(f"  文档数: {kb.document_count}")
            print(f"  总大小: {kb.total_size:,} 字节")
            print("\n此操作不可撤销!")
            
            confirm = input("\n确认删除? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("已取消删除")
                return 0
        
        # 删除知识库
        success = await manager.delete_knowledge_base(args.kb_id)
        
        if success:
            print(f"\n✓ 知识库已删除: {kb.name}")
            return 0
        else:
            logger.error("✗ 删除失败")
            return 1
        
    except KnowledgeBaseNotFoundError as e:
        logger.error(f"✗ {e}")
        return 1
    except Exception as e:
        logger.error(f"✗ 删除知识库失败: {e}", exc_info=args.verbose)
        return 1


async def cmd_upload(args):
    """上传文件到知识库"""
    logger = logging.getLogger(__name__)
    
    try:
        manager = get_manager()
        await manager.initialize()
        
        # 验证文件路径
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error(f"✗ 文件不存在: {args.file}")
            return 1
        
        # 上传文件
        file_entity = await manager.upload_file(
            kb_id=args.kb_id,
            file_path=str(file_path),
            file_name=args.name
        )
        
        print(f"\n✓ 文件上传成功!")
        print(f"  文件 ID: {file_entity.id}")
        print(f"  文件名: {file_entity.file_name}")
        print(f"  大小: {file_entity.file_size:,} 字节")
        print(f"  状态: {file_entity.status.value}")
        
        # 如果需要立即处理
        if args.process:
            print(f"\n开始处理文件...")
            processed_file = await manager.process_file(file_entity.id)
            
            print(f"\n✓ 文件处理完成!")
            print(f"  状态: {processed_file.status.value}")
            print(f"  块数: {processed_file.chunk_count}")
            
            if processed_file.status == FileStatus.FAILED:
                print(f"  失败原因: {processed_file.failed_reason}")
        
        if args.json:
            print(f"\nJSON 输出:")
            print(json.dumps({
                "id": file_entity.id,
                "file_name": file_entity.file_name,
                "file_size": file_entity.file_size,
                "status": file_entity.status.value,
                "created_at": file_entity.created_at.isoformat()
            }, indent=2, ensure_ascii=False))
        
        return 0
        
    except (KnowledgeBaseNotFoundError, FileValidationError) as e:
        logger.error(f"✗ {e}")
        return 1
    except Exception as e:
        logger.error(f"✗ 上传文件失败: {e}", exc_info=args.verbose)
        return 1


async def cmd_list_files(args):
    """列出知识库中的文件"""
    logger = logging.getLogger(__name__)
    
    try:
        manager = get_manager()
        await manager.initialize()
        
        # 解析状态过滤
        status_filter = None
        if args.status:
            try:
                status_filter = FileStatus(args.status)
            except ValueError:
                logger.error(f"✗ 无效的状态值: {args.status}")
                logger.error(f"  有效值: {', '.join([s.value for s in FileStatus])}")
                return 1
        
        # 列出文件
        files, total = await manager.list_files(
            kb_id=args.kb_id,
            status=status_filter,
            page=args.page,
            size=args.size
        )
        
        if not files:
            print("\n未找到文件")
            return 0
        
        print(f"\n文件列表 (共 {total} 个，当前第 {args.page} 页):")
        print("=" * 80)
        
        for file in files:
            print(f"\nID: {file.id}")
            print(f"文件名: {file.file_name}")
            print(f"大小: {file.file_size:,} 字节")
            print(f"状态: {file.status.value}")
            print(f"块数: {file.chunk_count}")
            print(f"上传时间: {file.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if file.status == FileStatus.FAILED and file.failed_reason:
                print(f"失败原因: {file.failed_reason}")
            
            print("-" * 80)
        
        # 分页信息
        total_pages = (total + args.size - 1) // args.size
        print(f"\n第 {args.page}/{total_pages} 页")
        
        if args.json:
            print(f"\nJSON 输出:")
            print(json.dumps({
                "total": total,
                "page": args.page,
                "size": args.size,
                "files": [
                    {
                        "id": file.id,
                        "file_name": file.file_name,
                        "file_size": file.file_size,
                        "status": file.status.value,
                        "chunk_count": file.chunk_count,
                        "created_at": file.created_at.isoformat()
                    }
                    for file in files
                ]
            }, indent=2, ensure_ascii=False))
        
        return 0
        
    except KnowledgeBaseNotFoundError as e:
        logger.error(f"✗ {e}")
        return 1
    except Exception as e:
        logger.error(f"✗ 列出文件失败: {e}", exc_info=args.verbose)
        return 1


async def cmd_delete_file(args):
    """删除文件"""
    logger = logging.getLogger(__name__)
    
    try:
        manager = get_manager()
        await manager.initialize()
        
        # 确认删除
        if not args.yes:
            print(f"\n警告: 即将删除文件 (ID: {args.file_id})")
            print("\n此操作不可撤销!")
            
            confirm = input("\n确认删除? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("已取消删除")
                return 0
        
        # 删除文件
        success = await manager.delete_file(args.kb_id, args.file_id)
        
        if success:
            print(f"\n✓ 文件已删除")
            return 0
        else:
            logger.error("✗ 删除失败")
            return 1
        
    except (KnowledgeBaseNotFoundError, FileValidationError) as e:
        logger.error(f"✗ {e}")
        return 1
    except Exception as e:
        logger.error(f"✗ 删除文件失败: {e}", exc_info=args.verbose)
        return 1


async def cmd_query(args):
    """查询知识库"""
    logger = logging.getLogger(__name__)
    
    try:
        manager = get_manager()
        await manager.initialize()
        
        # 查询知识库
        results = await manager.query_knowledge_base(
            kb_id=args.kb_id,
            query=args.query,
            top_k=args.top_k,
            similarity_threshold=args.similarity_threshold
        )
        
        if not results:
            print("\n未找到匹配结果")
            return 0
        
        print(f"\n查询结果 (共 {len(results)} 个):")
        print("=" * 80)
        
        for i, result in enumerate(results, 1):
            print(f"\n结果 {i}:")
            print(f"  分数: {result['score']:.4f}")
            print(f"  来源: {result['source']}")
            print(f"  文件 ID: {result['file_id']}")
            print(f"  块索引: {result['chunk_index']}")
            
            # 显示文本内容
            text = result['text']
            if len(text) > 200 and not args.full:
                text = text[:200] + "..."
            print(f"  内容: {text}")
            
            print("-" * 80)
        
        if args.json:
            print(f"\nJSON 输出:")
            print(json.dumps({
                "query": args.query,
                "total": len(results),
                "results": results
            }, indent=2, ensure_ascii=False))
        
        return 0
        
    except (KnowledgeBaseNotFoundError, ValueError) as e:
        logger.error(f"✗ {e}")
        return 1
    except Exception as e:
        logger.error(f"✗ 查询失败: {e}", exc_info=args.verbose)
        return 1


# ==================== 主函数 ====================

def main():
    """主函数 - 解析命令行参数并执行相应命令"""
    
    # 创建主解析器
    parser = argparse.ArgumentParser(
        description='RAG5 知识库管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 创建知识库
  python scripts/kb_manager.py create --name tech_docs \\
      --description "技术文档" --embedding-model nomic-embed-text

  # 列出所有知识库
  python scripts/kb_manager.py list

  # 获取知识库详情
  python scripts/kb_manager.py get --kb-id kb_123

  # 更新知识库
  python scripts/kb_manager.py update --kb-id kb_123 \\
      --description "更新的描述" --top-k 10

  # 删除知识库
  python scripts/kb_manager.py delete --kb-id kb_123 --yes

  # 上传文件
  python scripts/kb_manager.py upload --kb-id kb_123 \\
      --file /path/to/document.pdf --process

  # 列出文件
  python scripts/kb_manager.py list-files --kb-id kb_123 --status succeeded

  # 删除文件
  python scripts/kb_manager.py delete-file --kb-id kb_123 --file-id file_456 --yes

  # 查询知识库
  python scripts/kb_manager.py query --kb-id kb_123 \\
      --query "什么是人工智能？" --top-k 5
        """
    )
    
    # 全局参数
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='启用详细日志输出'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='以 JSON 格式输出结果'
    )
    
    # 创建子命令解析器
    subparsers = parser.add_subparsers(
        dest='command',
        help='可用命令',
        required=True
    )
    
    # ========== create 命令 ==========
    parser_create = subparsers.add_parser(
        'create',
        help='创建新知识库'
    )
    parser_create.add_argument(
        '--name',
        type=str,
        required=True,
        help='知识库名称（唯一，字母数字下划线连字符）'
    )
    parser_create.add_argument(
        '--description',
        type=str,
        help='知识库描述'
    )
    parser_create.add_argument(
        '--embedding-model',
        type=str,
        required=True,
        help='嵌入模型名称'
    )
    parser_create.add_argument(
        '--chunk-size',
        type=int,
        help='分块大小（默认: 512）'
    )
    parser_create.add_argument(
        '--chunk-overlap',
        type=int,
        help='分块重叠大小（默认: 50）'
    )
    parser_create.add_argument(
        '--parser-type',
        type=str,
        choices=['sentence', 'recursive', 'semantic'],
        help='解析器类型（默认: sentence）'
    )
    parser_create.add_argument(
        '--top-k',
        type=int,
        help='检索结果数量（默认: 5）'
    )
    parser_create.add_argument(
        '--similarity-threshold',
        type=float,
        help='相似度阈值（默认: 0.3）'
    )
    parser_create.add_argument(
        '--retrieval-mode',
        type=str,
        choices=['vector', 'fulltext', 'hybrid'],
        help='检索模式（默认: hybrid）'
    )
    parser_create.set_defaults(func=cmd_create)
    
    # ========== list 命令 ==========
    parser_list = subparsers.add_parser(
        'list',
        help='列出所有知识库'
    )
    parser_list.add_argument(
        '--page',
        type=int,
        default=1,
        help='页码（默认: 1）'
    )
    parser_list.add_argument(
        '--size',
        type=int,
        default=10,
        help='每页数量（默认: 10）'
    )
    parser_list.set_defaults(func=cmd_list)
    
    # ========== get 命令 ==========
    parser_get = subparsers.add_parser(
        'get',
        help='获取知识库详情'
    )
    parser_get.add_argument(
        '--kb-id',
        type=str,
        required=True,
        help='知识库 ID'
    )
    parser_get.set_defaults(func=cmd_get)
    
    # ========== update 命令 ==========
    parser_update = subparsers.add_parser(
        'update',
        help='更新知识库配置'
    )
    parser_update.add_argument(
        '--kb-id',
        type=str,
        required=True,
        help='知识库 ID'
    )
    parser_update.add_argument(
        '--name',
        type=str,
        help='新名称'
    )
    parser_update.add_argument(
        '--description',
        type=str,
        help='新描述'
    )
    parser_update.add_argument(
        '--embedding-model',
        type=str,
        help='新嵌入模型（警告：需要重新嵌入现有文档）'
    )
    parser_update.add_argument(
        '--chunk-size',
        type=int,
        help='新分块大小'
    )
    parser_update.add_argument(
        '--chunk-overlap',
        type=int,
        help='新分块重叠大小'
    )
    parser_update.add_argument(
        '--parser-type',
        type=str,
        choices=['sentence', 'recursive', 'semantic'],
        help='新解析器类型'
    )
    parser_update.add_argument(
        '--top-k',
        type=int,
        help='新检索结果数量'
    )
    parser_update.add_argument(
        '--similarity-threshold',
        type=float,
        help='新相似度阈值'
    )
    parser_update.add_argument(
        '--retrieval-mode',
        type=str,
        choices=['vector', 'fulltext', 'hybrid'],
        help='新检索模式'
    )
    parser_update.set_defaults(func=cmd_update)
    
    # ========== delete 命令 ==========
    parser_delete = subparsers.add_parser(
        'delete',
        help='删除知识库'
    )
    parser_delete.add_argument(
        '--kb-id',
        type=str,
        required=True,
        help='知识库 ID'
    )
    parser_delete.add_argument(
        '--yes',
        action='store_true',
        help='跳过确认提示'
    )
    parser_delete.set_defaults(func=cmd_delete)
    
    # ========== upload 命令 ==========
    parser_upload = subparsers.add_parser(
        'upload',
        help='上传文件到知识库'
    )
    parser_upload.add_argument(
        '--kb-id',
        type=str,
        required=True,
        help='知识库 ID'
    )
    parser_upload.add_argument(
        '--file',
        type=str,
        required=True,
        help='文件路径'
    )
    parser_upload.add_argument(
        '--name',
        type=str,
        help='自定义文件名（可选）'
    )
    parser_upload.add_argument(
        '--process',
        action='store_true',
        help='立即处理文件'
    )
    parser_upload.set_defaults(func=cmd_upload)
    
    # ========== list-files 命令 ==========
    parser_list_files = subparsers.add_parser(
        'list-files',
        help='列出知识库中的文件'
    )
    parser_list_files.add_argument(
        '--kb-id',
        type=str,
        required=True,
        help='知识库 ID'
    )
    parser_list_files.add_argument(
        '--status',
        type=str,
        choices=['pending', 'parsing', 'persisting', 'succeeded', 'failed', 'cancelled'],
        help='按状态过滤'
    )
    parser_list_files.add_argument(
        '--page',
        type=int,
        default=1,
        help='页码（默认: 1）'
    )
    parser_list_files.add_argument(
        '--size',
        type=int,
        default=10,
        help='每页数量（默认: 10）'
    )
    parser_list_files.set_defaults(func=cmd_list_files)
    
    # ========== delete-file 命令 ==========
    parser_delete_file = subparsers.add_parser(
        'delete-file',
        help='删除文件'
    )
    parser_delete_file.add_argument(
        '--kb-id',
        type=str,
        required=True,
        help='知识库 ID'
    )
    parser_delete_file.add_argument(
        '--file-id',
        type=str,
        required=True,
        help='文件 ID'
    )
    parser_delete_file.add_argument(
        '--yes',
        action='store_true',
        help='跳过确认提示'
    )
    parser_delete_file.set_defaults(func=cmd_delete_file)
    
    # ========== query 命令 ==========
    parser_query = subparsers.add_parser(
        'query',
        help='查询知识库'
    )
    parser_query.add_argument(
        '--kb-id',
        type=str,
        required=True,
        help='知识库 ID'
    )
    parser_query.add_argument(
        '--query',
        type=str,
        required=True,
        help='查询文本'
    )
    parser_query.add_argument(
        '--top-k',
        type=int,
        help='返回结果数量（可选，使用知识库配置）'
    )
    parser_query.add_argument(
        '--similarity-threshold',
        type=float,
        help='相似度阈值（可选，使用知识库配置）'
    )
    parser_query.add_argument(
        '--full',
        action='store_true',
        help='显示完整文本内容'
    )
    parser_query.set_defaults(func=cmd_query)
    
    # 解析参数
    args = parser.parse_args()
    
    # 配置日志
    setup_logging(args.verbose)
    
    # 执行命令
    try:
        exit_code = asyncio.run(args.func(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(130)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"执行失败: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()
