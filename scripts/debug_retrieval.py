#!/usr/bin/env python3
"""
检索调试脚本

提供完整的调试流程：检查数据库 -> 验证嵌入 -> 测试查询 -> 生成报告
针对"于朦朧"查询进行专门测试，输出详细的诊断信息和建议。

使用方法:
    python scripts/debug_retrieval.py
    python scripts/debug_retrieval.py --query "于朦朧是怎么死的"
    python scripts/debug_retrieval.py --collection knowledge_base --keyword "于朦朧"
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag5.config import settings
from rag5.utils.logging_config import RAGLogger
from rag5.tools.diagnostics import QdrantInspector
from rag5.tools.embeddings import OllamaEmbeddingsManager
from rag5.tools.vectordb import QdrantManager
from rag5.tools.search import AdaptiveSearchTool, HybridSearchTool

# 配置日志
RAGLogger.setup_logging(
    log_level="DEBUG",
    log_file=None,  # 仅输出到控制台
    enable_console=True
)
logger = logging.getLogger(__name__)


class RetrievalDebugger:
    """
    检索调试器
    
    提供完整的调试流程，包括数据库检查、嵌入验证、查询测试和问题诊断。
    """
    
    def __init__(
        self,
        collection_name: Optional[str] = None,
        qdrant_url: Optional[str] = None
    ):
        """
        初始化调试器
        
        参数:
            collection_name: 集合名称（默认使用配置中的值）
            qdrant_url: Qdrant URL（默认使用配置中的值）
        """
        self.collection_name = collection_name or settings.collection_name
        self.qdrant_url = qdrant_url or settings.qdrant_url
        
        # 初始化管理器
        self.qdrant_manager = QdrantManager(url=self.qdrant_url)
        self.embeddings_manager = OllamaEmbeddingsManager(
            model=settings.embed_model,
            base_url=settings.ollama_host
        )
        self.embeddings_manager.initialize()
        
        # 初始化检查器
        self.inspector = QdrantInspector(
            self.qdrant_manager,
            self.embeddings_manager
        )
        
        # 初始化搜索工具
        self.adaptive_search = AdaptiveSearchTool(
            self.embeddings_manager,
            self.qdrant_manager,
            self.collection_name
        )
        
        self.hybrid_search = HybridSearchTool(
            self.embeddings_manager,
            self.qdrant_manager,
            self.collection_name
        )
        
        # 诊断结果
        self.issues: List[Dict[str, Any]] = []
        self.recommendations: List[str] = []
    
    def print_header(self, title: str):
        """打印标题"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")
    
    def print_section(self, title: str):
        """打印章节标题"""
        print(f"\n{'─' * 80}")
        print(f"  {title}")
        print(f"{'─' * 80}\n")
    
    def check_database_status(self) -> Dict[str, Any]:
        """
        检查数据库状态
        
        返回:
            数据库状态信息
        """
        self.print_section("1. 数据库状态检查")
        
        # 获取集合统计
        stats = self.inspector.get_collection_stats(self.collection_name)
        
        print(f"集合名称: {self.collection_name}")
        print(f"Qdrant URL: {self.qdrant_url}")
        print()
        
        if not stats['exists']:
            print("❌ 集合不存在")
            self.issues.append({
                "type": "database_empty",
                "severity": "critical",
                "message": f"集合 '{self.collection_name}' 不存在"
            })
            self.recommendations.append(
                f"运行索引命令创建集合并索引文档:\n"
                f"  python -m rag5.tools.index_manager reindex --directory ./docs --collection {self.collection_name}"
            )
            return stats
        
        print(f"✓ 集合存在")
        print(f"  - 状态: {stats['status']}")
        print(f"  - 点数量: {stats['points_count']}")
        print(f"  - 向量数量: {stats['vectors_count']}")
        print(f"  - 已索引向量: {stats['indexed_vectors_count']}")
        
        # 检查是否为空
        if stats['points_count'] == 0:
            print("\n❌ 数据库为空，没有索引任何文档")
            self.issues.append({
                "type": "database_empty",
                "severity": "critical",
                "message": "数据库中没有任何文档"
            })
            self.recommendations.append(
                "索引文档到数据库:\n"
                f"  python scripts/ingest.py --directory ./docs"
            )
        else:
            print(f"\n✓ 数据库包含 {stats['points_count']} 个文档分块")
        
        # 获取样本数据
        print("\n获取样本数据...")
        samples = self.inspector.get_sample_points(self.collection_name, limit=3)
        
        if samples:
            print(f"\n样本数据 (前 {len(samples)} 个):")
            for i, sample in enumerate(samples, 1):
                print(f"\n  样本 {i}:")
                print(f"    - ID: {sample['id']}")
                print(f"    - 向量维度: {sample['vector_dim']}")
                print(f"    - 包含文本: {'是' if sample['has_text'] else '否'}")
                print(f"    - 包含来源: {'是' if sample['has_source'] else '否'}")
                if sample['text_preview']:
                    preview = sample['text_preview'].replace('\n', ' ')
                    print(f"    - 文本预览: {preview}...")
        
        return stats
    
    def search_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索关键词
        
        参数:
            keyword: 搜索关键词
        
        返回:
            搜索结果列表
        """
        self.print_section(f"2. 关键词搜索测试: '{keyword}'")
        
        print(f"在数据库中搜索关键词 '{keyword}'...")
        results = self.inspector.search_by_keyword(
            self.collection_name,
            keyword,
            limit=10
        )
        
        if not results:
            print(f"\n❌ 未找到包含 '{keyword}' 的文档")
            self.issues.append({
                "type": "keyword_not_found",
                "severity": "high",
                "message": f"数据库中不包含关键词 '{keyword}'"
            })
            self.recommendations.append(
                f"确认文档中是否包含 '{keyword}'，如果包含，请重新索引:\n"
                f"  python -m rag5.tools.index_manager reindex --directory ./docs --force"
            )
        else:
            print(f"\n✓ 找到 {len(results)} 个包含 '{keyword}' 的文档分块")
            for i, result in enumerate(results[:5], 1):  # 只显示前5个
                print(f"\n  结果 {i}:")
                print(f"    - 来源: {result['source']}")
                print(f"    - 出现次数: {result['keyword_count']}")
                print(f"    - 文本片段: {result['text']}")
        
        return results
    
    def verify_embeddings(self) -> Dict[str, Any]:
        """
        验证嵌入模型
        
        返回:
            验证结果
        """
        self.print_section("3. 嵌入模型验证")
        
        print(f"验证嵌入模型: {settings.embed_model}")
        print(f"Ollama 地址: {settings.ollama_host}")
        print()
        
        # 测试文本
        test_texts = [
            "这是一个测试文本",
            "人工智能是什么？",
            "于朦朧是谁？"
        ]
        
        result = self.inspector.verify_embeddings(
            self.collection_name,
            test_texts
        )
        
        if result['model_working']:
            print(f"✓ 嵌入模型工作正常")
            print(f"  - 模型名称: {result['model_name']}")
            print(f"  - 向量维度: {result['vector_dim']}")
            print(f"  - 期望维度: {result['expected_dim']}")
            print(f"  - 维度匹配: {'是' if result['dimension_match'] else '否'}")
            print(f"  - 平均生成时间: {result['average_time']:.3f}秒")
            print(f"  - 成功测试: {result['successful_tests']}/{result['total_tests']}")
        else:
            print(f"❌ 嵌入模型验证失败")
            print(f"  - 错误: {result.get('error', '未知错误')}")
            self.issues.append({
                "type": "embedding_model_error",
                "severity": "critical",
                "message": f"嵌入模型验证失败: {result.get('error')}"
            })
            self.recommendations.append(
                "检查 Ollama 服务是否运行:\n"
                "  curl http://localhost:11434/api/tags\n"
                f"确认模型 '{settings.embed_model}' 已安装:\n"
                f"  ollama pull {settings.embed_model}"
            )
        
        # 显示测试详情
        if result.get('test_results'):
            print("\n测试详情:")
            for i, test in enumerate(result['test_results'], 1):
                status = "✓" if test['success'] else "✗"
                print(f"  {status} 测试 {i}: {test['text']}")
                if test['success']:
                    print(f"      维度: {test['vector_dim']}, 耗时: {test['time']:.3f}秒")
                else:
                    print(f"      错误: {test['error']}")
        
        return result
    
    def test_query(
        self,
        query: str,
        test_thresholds: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        测试查询
        
        参数:
            query: 查询文本
            test_thresholds: 要测试的阈值列表
        
        返回:
            测试结果
        """
        self.print_section(f"4. 查询测试: '{query}'")
        
        if test_thresholds is None:
            test_thresholds = [0.7, 0.5, 0.3, 0.1]
        
        print(f"查询: {query}")
        print(f"测试阈值: {test_thresholds}")
        print()
        
        # 测试不同阈值
        print("测试不同相似度阈值...")
        stats = self.adaptive_search.get_search_statistics(query, test_thresholds)
        
        if 'error' in stats:
            print(f"❌ 查询测试失败: {stats['error']}")
            return stats
        
        print("\n阈值测试结果:")
        print(f"{'阈值':<10} {'结果数':<10} {'平均分数':<15}")
        print("-" * 40)
        
        for threshold in sorted(test_thresholds, reverse=True):
            result_info = stats['results_by_threshold'].get(threshold, {})
            count = result_info.get('count', 0)
            avg_score = result_info.get('avg_score', 0)
            print(f"{threshold:<10.2f} {count:<10} {avg_score:<15.4f}")
        
        # 使用自适应搜索
        print(f"\n使用自适应搜索 (初始阈值: {settings.similarity_threshold})...")
        adaptive_results = self.adaptive_search.search_with_fallback(
            query=query,
            initial_threshold=settings.similarity_threshold,
            min_threshold=settings.min_similarity_threshold,
            target_results=settings.target_results
        )
        
        if not adaptive_results:
            print(f"\n❌ 自适应搜索未找到结果")
            self.issues.append({
                "type": "no_results",
                "severity": "high",
                "message": f"查询 '{query}' 未返回任何结果"
            })
            self.recommendations.append(
                "可能的原因和解决方案:\n"
                "  1. 相似度阈值过高 - 尝试降低 SIMILARITY_THRESHOLD\n"
                "  2. 文档未正确索引 - 重新索引文档\n"
                "  3. 查询词不匹配 - 尝试使用不同的查询词\n"
                "  4. 嵌入模型不兼容 - 检查模型是否支持中文"
            )
        else:
            print(f"\n✓ 找到 {len(adaptive_results)} 个结果")
            for i, result in enumerate(adaptive_results[:3], 1):  # 显示前3个
                print(f"\n  结果 {i}:")
                print(f"    - 相似度分数: {result['score']:.4f}")
                print(f"    - 来源: {result['source']}")
                content_preview = result['content'][:200].replace('\n', ' ')
                print(f"    - 内容: {content_preview}...")
        
        # 如果启用混合搜索，也测试混合搜索
        if settings.enable_hybrid_search:
            print(f"\n使用混合搜索...")
            hybrid_results = self.hybrid_search.hybrid_search(
                query=query,
                vector_weight=settings.vector_search_weight,
                keyword_weight=settings.keyword_search_weight
            )
            
            if hybrid_results:
                print(f"✓ 混合搜索找到 {len(hybrid_results)} 个结果")
                for i, result in enumerate(hybrid_results[:3], 1):
                    print(f"\n  结果 {i}:")
                    print(f"    - 综合分数: {result['score']:.4f}")
                    print(f"    - 来源: {result['source']}")
                    content_preview = result['content'][:200].replace('\n', ' ')
                    print(f"    - 内容: {content_preview}...")
        
        return {
            "statistics": stats,
            "adaptive_results": adaptive_results,
            "hybrid_results": hybrid_results if settings.enable_hybrid_search else None
        }
    
    def diagnose_issues(self):
        """诊断问题并提供建议"""
        self.print_section("5. 问题诊断和建议")
        
        if not self.issues:
            print("✓ 未发现明显问题")
            print("\n系统状态良好，检索功能正常工作。")
            return
        
        print(f"发现 {len(self.issues)} 个问题:\n")
        
        # 按严重程度分组
        critical_issues = [i for i in self.issues if i['severity'] == 'critical']
        high_issues = [i for i in self.issues if i['severity'] == 'high']
        medium_issues = [i for i in self.issues if i['severity'] == 'medium']
        
        if critical_issues:
            print("🔴 严重问题:")
            for i, issue in enumerate(critical_issues, 1):
                print(f"  {i}. [{issue['type']}] {issue['message']}")
            print()
        
        if high_issues:
            print("🟠 高优先级问题:")
            for i, issue in enumerate(high_issues, 1):
                print(f"  {i}. [{issue['type']}] {issue['message']}")
            print()
        
        if medium_issues:
            print("🟡 中等优先级问题:")
            for i, issue in enumerate(medium_issues, 1):
                print(f"  {i}. [{issue['type']}] {issue['message']}")
            print()
        
        # 提供建议
        if self.recommendations:
            print("\n建议的解决方案:\n")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"{i}. {rec}")
                print()
    
    def generate_report(self) -> str:
        """
        生成诊断报告
        
        返回:
            报告文本
        """
        self.print_section("6. 诊断报告")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
检索系统诊断报告
生成时间: {timestamp}
集合名称: {self.collection_name}
Qdrant URL: {self.qdrant_url}

配置信息:
  - 嵌入模型: {settings.embed_model}
  - 相似度阈值: {settings.similarity_threshold}
  - Top K: {settings.top_k}
  - 混合搜索: {'启用' if settings.enable_hybrid_search else '禁用'}
  - 中文分块器: {'启用' if settings.enable_chinese_splitter else '禁用'}

问题总数: {len(self.issues)}
  - 严重: {len([i for i in self.issues if i['severity'] == 'critical'])}
  - 高优先级: {len([i for i in self.issues if i['severity'] == 'high'])}
  - 中等优先级: {len([i for i in self.issues if i['severity'] == 'medium'])}

建议数量: {len(self.recommendations)}
"""
        
        print(report)
        
        # 保存报告到文件
        report_dir = project_root / "logs"
        report_dir.mkdir(exist_ok=True)
        report_file = report_dir / f"debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
            f.write("\n详细问题列表:\n")
            for i, issue in enumerate(self.issues, 1):
                f.write(f"\n{i}. [{issue['severity'].upper()}] {issue['type']}\n")
                f.write(f"   {issue['message']}\n")
            
            f.write("\n建议的解决方案:\n")
            for i, rec in enumerate(self.recommendations, 1):
                f.write(f"\n{i}. {rec}\n")
        
        print(f"\n报告已保存到: {report_file}")
        
        return report
    
    def run_full_diagnostic(
        self,
        test_query: str = "于朦朧是怎么死的",
        test_keyword: str = "于朦朧"
    ):
        """
        运行完整的诊断流程
        
        参数:
            test_query: 测试查询
            test_keyword: 测试关键词
        """
        self.print_header("RAG5 检索系统诊断工具")
        
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试查询: {test_query}")
        print(f"测试关键词: {test_keyword}")
        
        try:
            # 1. 检查数据库状态
            db_stats = self.check_database_status()
            
            # 如果数据库不存在或为空，跳过后续测试
            if not db_stats.get('exists') or db_stats.get('points_count', 0) == 0:
                self.diagnose_issues()
                self.generate_report()
                return
            
            # 2. 搜索关键词
            keyword_results = self.search_keyword(test_keyword)
            
            # 3. 验证嵌入模型
            embedding_result = self.verify_embeddings()
            
            # 如果嵌入模型有问题，跳过查询测试
            if not embedding_result.get('model_working'):
                self.diagnose_issues()
                self.generate_report()
                return
            
            # 4. 测试查询
            query_results = self.test_query(test_query)
            
            # 5. 诊断问题
            self.diagnose_issues()
            
            # 6. 生成报告
            self.generate_report()
            
        except Exception as e:
            logger.error(f"诊断过程中发生错误: {e}", exc_info=True)
            print(f"\n❌ 诊断失败: {e}")
            self.issues.append({
                "type": "diagnostic_error",
                "severity": "critical",
                "message": f"诊断过程中发生错误: {str(e)}"
            })
            self.generate_report()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="RAG5 检索系统调试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行完整诊断（使用默认查询）
  python scripts/debug_retrieval.py
  
  # 使用自定义查询
  python scripts/debug_retrieval.py --query "李小勇是谁"
  
  # 使用自定义关键词
  python scripts/debug_retrieval.py --keyword "李小勇"
  
  # 指定集合名称
  python scripts/debug_retrieval.py --collection my_collection
        """
    )
    
    parser.add_argument(
        '--query',
        type=str,
        default="于朦朧是怎么死的",
        help="测试查询（默认: 于朦朧是怎么死的）"
    )
    
    parser.add_argument(
        '--keyword',
        type=str,
        default="于朦朧",
        help="测试关键词（默认: 于朦朧）"
    )
    
    parser.add_argument(
        '--collection',
        type=str,
        default=None,
        help=f"集合名称（默认: {settings.collection_name}）"
    )
    
    parser.add_argument(
        '--qdrant-url',
        type=str,
        default=None,
        help=f"Qdrant URL（默认: {settings.qdrant_url}）"
    )
    
    args = parser.parse_args()
    
    try:
        # 创建调试器
        debugger = RetrievalDebugger(
            collection_name=args.collection,
            qdrant_url=args.qdrant_url
        )
        
        # 运行完整诊断
        debugger.run_full_diagnostic(
            test_query=args.query,
            test_keyword=args.keyword
        )
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行失败: {e}", exc_info=True)
        print(f"\n❌ 程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
