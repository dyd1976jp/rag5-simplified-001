"""
数据库检查命令行工具

提供命令行接口用于检查和诊断 Qdrant 向量数据库。
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from rag5.config import settings
from rag5.tools.vectordb import QdrantManager
from rag5.tools.embeddings import OllamaEmbeddingsManager
from rag5.tools.diagnostics import QdrantInspector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def print_separator(char='=', length=80):
    """打印分隔线"""
    print(char * length)


def print_section_header(title: str):
    """打印章节标题"""
    print()
    print_separator()
    print(f"  {title}")
    print_separator()
    print()


def format_stats(stats: dict) -> str:
    """格式化统计信息"""
    if not stats.get('exists'):
        return "❌ 集合不存在"
    
    lines = [
        f"✓ 集合状态: {stats['status']}",
        f"  - 点数量: {stats['points_count']:,}",
        f"  - 向量数量: {stats['vectors_count']:,}",
        f"  - 已索引向量: {stats['indexed_vectors_count']:,}"
    ]
    return "\n".join(lines)


def format_keyword_results(results: list, keyword: str) -> str:
    """格式化关键词搜索结果"""
    if not results:
        return f"❌ 未找到包含关键词 '{keyword}' 的结果"
    
    lines = [f"✓ 找到 {len(results)} 个包含关键词 '{keyword}' 的结果:\n"]
    
    for i, result in enumerate(results, 1):
        lines.append(f"{i}. ID: {result['id']}")
        lines.append(f"   来源: {result['source']}")
        lines.append(f"   出现次数: {result['keyword_count']}")
        lines.append(f"   文本预览: {result['text']}")
        lines.append("")
    
    return "\n".join(lines)


def format_samples(samples: list) -> str:
    """格式化样本数据"""
    if not samples:
        return "❌ 未获取到样本数据"
    
    lines = [f"✓ 获取了 {len(samples)} 个样本数据点:\n"]
    
    for i, sample in enumerate(samples, 1):
        lines.append(f"{i}. ID: {sample['id']}")
        lines.append(f"   向量维度: {sample['vector_dim']}")
        lines.append(f"   有文本: {'✓' if sample['has_text'] else '✗'}")
        lines.append(f"   有来源: {'✓' if sample['has_source'] else '✗'}")
        
        if sample.get('text_preview'):
            lines.append(f"   文本预览: {sample['text_preview']}...")
        
        if sample['payload']:
            lines.append(f"   Payload 键: {', '.join(sample['payload'].keys())}")
        
        lines.append("")
    
    return "\n".join(lines)


def format_embedding_verification(result: dict) -> str:
    """格式化嵌入验证结果"""
    if not result.get('model_working'):
        error = result.get('error', '未知错误')
        return f"❌ 嵌入模型验证失败: {error}"
    
    lines = [
        f"✓ 嵌入模型验证成功",
        f"  - 模型名称: {result['model_name']}",
        f"  - 向量维度: {result['vector_dim']}",
        f"  - 期望维度: {result['expected_dim']}",
        f"  - 维度匹配: {'✓' if result['dimension_match'] else '✗'}",
        f"  - 成功测试: {result['successful_tests']}/{result['total_tests']}",
        f"  - 平均时间: {result['average_time']:.3f}s",
        ""
    ]
    
    # 显示测试详情
    if result.get('test_results'):
        lines.append("测试详情:")
        for i, test in enumerate(result['test_results'], 1):
            status = "✓" if test['success'] else "✗"
            lines.append(f"  {i}. {status} '{test['text'][:30]}...'")
            if test['success']:
                lines.append(f"     维度={test['vector_dim']}, 时间={test['time']:.3f}s")
            else:
                lines.append(f"     错误: {test['error']}")
    
    return "\n".join(lines)


def check_collection_stats(
    inspector: QdrantInspector,
    collection_name: str
):
    """检查集合统计信息"""
    print_section_header(f"集合统计信息: {collection_name}")
    
    stats = inspector.get_collection_stats(collection_name)
    print(format_stats(stats))
    
    return stats


def search_keyword(
    inspector: QdrantInspector,
    collection_name: str,
    keyword: str,
    limit: int
):
    """搜索关键词"""
    print_section_header(f"关键词搜索: '{keyword}'")
    
    results = inspector.search_by_keyword(collection_name, keyword, limit)
    print(format_keyword_results(results, keyword))
    
    return results


def get_samples(
    inspector: QdrantInspector,
    collection_name: str,
    limit: int
):
    """获取样本数据"""
    print_section_header(f"样本数据 (limit={limit})")
    
    samples = inspector.get_sample_points(collection_name, limit)
    print(format_samples(samples))
    
    return samples


def verify_embeddings(
    inspector: QdrantInspector,
    collection_name: str
):
    """验证嵌入模型"""
    print_section_header("嵌入模型验证")
    
    result = inspector.verify_embeddings(collection_name)
    print(format_embedding_verification(result))
    
    return result


def generate_diagnostic_report(
    collection_name: str,
    stats: dict,
    keyword_results: Optional[list] = None,
    samples: Optional[list] = None,
    embedding_result: Optional[dict] = None
):
    """生成诊断报告"""
    print_section_header("诊断报告")
    
    issues = []
    recommendations = []
    
    # 检查集合状态
    if not stats.get('exists'):
        issues.append("集合不存在")
        recommendations.append(f"创建集合: python -m rag5.interfaces.cli ingest <directory>")
    elif stats['points_count'] == 0:
        issues.append("集合为空，没有数据")
        recommendations.append(f"索引文档: python -m rag5.interfaces.cli ingest <directory>")
    
    # 检查关键词搜索结果
    if keyword_results is not None and len(keyword_results) == 0:
        issues.append("关键词搜索无结果")
        recommendations.append("检查文档是否包含该关键词")
        recommendations.append("尝试重新索引文档")
    
    # 检查样本数据
    if samples is not None:
        if len(samples) == 0:
            issues.append("无法获取样本数据")
        else:
            # 检查样本质量
            has_text_count = sum(1 for s in samples if s['has_text'])
            has_source_count = sum(1 for s in samples if s['has_source'])
            
            if has_text_count == 0:
                issues.append("样本数据中没有文本内容")
                recommendations.append("检查文档摄取流程是否正确保存了文本")
            
            if has_source_count == 0:
                issues.append("样本数据中没有来源信息")
                recommendations.append("检查文档摄取流程是否正确保存了来源")
    
    # 检查嵌入模型
    if embedding_result is not None:
        if not embedding_result.get('model_working'):
            issues.append(f"嵌入模型异常: {embedding_result.get('error')}")
            recommendations.append(f"检查 Ollama 服务是否运行: ollama serve")
            recommendations.append(f"检查模型是否已下载: ollama pull {embedding_result.get('model_name', 'bge-m3')}")
        elif not embedding_result.get('dimension_match'):
            issues.append(
                f"向量维度不匹配 "
                f"(期望={embedding_result['expected_dim']}, "
                f"实际={embedding_result['vector_dim']})"
            )
            recommendations.append("重新索引文档以匹配当前模型的向量维度")
    
    # 打印诊断结果
    if issues:
        print("发现的问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. ❌ {issue}")
        print()
    else:
        print("✓ 未发现明显问题")
        print()
    
    if recommendations:
        print("建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        print()
    
    # 打印总结
    print_separator('-')
    if issues:
        print(f"状态: ❌ 发现 {len(issues)} 个问题")
    else:
        print("状态: ✓ 系统正常")
    print_separator('-')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Qdrant 数据库检查和诊断工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检查集合统计信息
  python -m rag5.tools.diagnostics.db_check --collection knowledge_base
  
  # 搜索关键词
  python -m rag5.tools.diagnostics.db_check --collection knowledge_base --search "于朦朧"
  
  # 获取样本数据
  python -m rag5.tools.diagnostics.db_check --collection knowledge_base --samples 10
  
  # 验证嵌入模型
  python -m rag5.tools.diagnostics.db_check --collection knowledge_base --verify-embeddings
  
  # 完整诊断（所有检查）
  python -m rag5.tools.diagnostics.db_check --collection knowledge_base --all
        """
    )
    
    parser.add_argument(
        '--collection',
        type=str,
        default=None,
        help=f'集合名称 (默认: {settings.collection_name})'
    )
    
    parser.add_argument(
        '--search',
        type=str,
        default=None,
        help='搜索关键词'
    )
    
    parser.add_argument(
        '--samples',
        type=int,
        default=None,
        help='获取样本数据的数量'
    )
    
    parser.add_argument(
        '--verify-embeddings',
        action='store_true',
        help='验证嵌入模型'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='执行所有检查'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试日志'
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 获取集合名称
    collection_name = args.collection or settings.collection_name
    
    # 打印配置信息
    print_section_header("配置信息")
    print(f"Qdrant URL: {settings.qdrant_url}")
    print(f"集合名称: {collection_name}")
    print(f"嵌入模型: {settings.embed_model}")
    print(f"Ollama Host: {settings.ollama_host}")
    
    try:
        # 初始化管理器
        logger.info("初始化 Qdrant 管理器...")
        qdrant_manager = QdrantManager(settings.qdrant_url)
        
        # 测试连接
        if not qdrant_manager.test_connection():
            logger.error(f"无法连接到 Qdrant 服务: {settings.qdrant_url}")
            print(f"\n❌ 无法连接到 Qdrant 服务: {settings.qdrant_url}")
            print("请确保 Qdrant 正在运行")
            sys.exit(1)
        
        logger.info("✓ Qdrant 连接成功")
        
        # 初始化嵌入管理器（如果需要）
        embeddings_manager = None
        if args.verify_embeddings or args.all:
            logger.info("初始化嵌入模型管理器...")
            embeddings_manager = OllamaEmbeddingsManager(
                model=settings.embed_model,
                base_url=settings.ollama_host
            )
        
        # 创建检查器
        inspector = QdrantInspector(qdrant_manager, embeddings_manager)
        
        # 执行检查
        stats = None
        keyword_results = None
        samples = None
        embedding_result = None
        
        # 1. 集合统计（总是执行）
        stats = check_collection_stats(inspector, collection_name)
        
        # 2. 关键词搜索
        if args.search or args.all:
            keyword = args.search or "于朦朧"
            limit = 10
            keyword_results = search_keyword(inspector, collection_name, keyword, limit)
        
        # 3. 样本数据
        if args.samples is not None or args.all:
            limit = args.samples if args.samples is not None else 5
            samples = get_samples(inspector, collection_name, limit)
        
        # 4. 嵌入验证
        if args.verify_embeddings or args.all:
            embedding_result = verify_embeddings(inspector, collection_name)
        
        # 5. 生成诊断报告
        if args.all or (args.search and args.samples and args.verify_embeddings):
            generate_diagnostic_report(
                collection_name,
                stats,
                keyword_results,
                samples,
                embedding_result
            )
        
        print()
        logger.info("检查完成")
        
    except KeyboardInterrupt:
        print("\n\n中断操作")
        sys.exit(0)
    except Exception as e:
        logger.error(f"检查失败: {e}", exc_info=args.debug)
        print(f"\n❌ 检查失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
