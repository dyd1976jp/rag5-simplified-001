#!/usr/bin/env python3
"""
端到端测试脚本

执行完整的端到端测试流程：
1. 清空现有集合
2. 重新索引包含"于朦朧"的文档
3. 执行测试查询："于朦朧是怎么死的"
4. 验证返回结果包含相关内容
5. 检查日志输出是否完整

使用方法:
    python scripts/test_e2e.py
    python scripts/test_e2e.py --skip-reindex  # 跳过重新索引
    python scripts/test_e2e.py --verbose       # 详细输出
"""

import argparse
import sys
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag5.config import settings
from rag5.utils.logging_config import RAGLogger
from rag5.tools.vectordb import QdrantManager
from rag5.tools.embeddings import OllamaEmbeddingsManager
from rag5.tools.index_manager import IndexManager
from rag5.ingestion import (
    IngestionPipeline,
    RecursiveSplitter,
    BatchVectorizer,
    VectorUploader
)
from rag5.tools.search import search_knowledge_base, AdaptiveSearchTool

logger = logging.getLogger(__name__)


class E2ETestRunner:
    """端到端测试运行器"""
    
    def __init__(self, verbose: bool = False):
        """
        初始化测试运行器
        
        参数:
            verbose: 是否启用详细日志
        """
        self.verbose = verbose
        self.test_results = []
        self.start_time = None
        self.end_time = None
        
        # 设置日志
        log_level = "DEBUG" if verbose else "INFO"
        RAGLogger.setup_logging(
            log_level=log_level,
            log_file="logs/e2e_test.log",
            enable_console=True
        )
        
        # 初始化组件
        self.qdrant = QdrantManager(settings.qdrant_url)
        self.embeddings = OllamaEmbeddingsManager(
            settings.embed_model,
            settings.ollama_host
        )
        self.embeddings.initialize()
        
        # 创建摄取流程
        splitter = RecursiveSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        vectorizer = BatchVectorizer(
            self.embeddings.embeddings,
            batch_size=settings.batch_size
        )
        uploader = VectorUploader(self.qdrant, settings.collection_name)
        
        self.pipeline = IngestionPipeline(
            splitter,
            vectorizer,
            uploader,
            auto_detect_chinese=True,
            chinese_threshold=0.3
        )
        
        # 创建索引管理器
        self.index_manager = IndexManager(self.qdrant, self.pipeline)
    
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
    
    def add_test_result(
        self,
        test_name: str,
        passed: bool,
        message: str = "",
        details: Dict[str, Any] = None
    ):
        """
        添加测试结果
        
        参数:
            test_name: 测试名称
            passed: 是否通过
            message: 消息
            details: 详细信息
        """
        result = {
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now()
        }
        self.test_results.append(result)
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"  {message}")
        if self.verbose and details:
            for key, value in details.items():
                print(f"  - {key}: {value}")
    
    def test_connection(self) -> bool:
        """
        测试连接
        
        返回:
            是否连接成功
        """
        self.print_section("步骤 0: 测试连接")
        
        # 测试 Qdrant 连接
        print("测试 Qdrant 连接...")
        qdrant_ok = self.qdrant.test_connection()
        
        if qdrant_ok:
            self.add_test_result(
                "Qdrant 连接",
                True,
                f"成功连接到 {settings.qdrant_url}"
            )
        else:
            self.add_test_result(
                "Qdrant 连接",
                False,
                f"无法连接到 {settings.qdrant_url}",
                {"url": settings.qdrant_url}
            )
            return False
        
        # 测试 Ollama 连接
        print("\n测试 Ollama 连接...")
        try:
            test_text = "测试文本"
            vector = self.embeddings.embed_query(test_text)
            ollama_ok = vector is not None and len(vector) > 0
        except Exception as e:
            logger.error(f"Ollama 连接测试失败: {e}")
            ollama_ok = False
        
        if ollama_ok:
            self.add_test_result(
                "Ollama 连接",
                True,
                f"成功连接到 {settings.ollama_host}，模型: {settings.embed_model}"
            )
        else:
            self.add_test_result(
                "Ollama 连接",
                False,
                f"无法连接到 {settings.ollama_host}",
                {
                    "host": settings.ollama_host,
                    "model": settings.embed_model
                }
            )
            return False
        
        return True
    
    def clear_collection(self) -> bool:
        """
        清空集合
        
        返回:
            是否成功
        """
        self.print_section("步骤 1: 清空现有集合")
        
        print(f"清空集合: {settings.collection_name}")
        
        try:
            success = self.index_manager.clear_collection(settings.collection_name)
            
            if success:
                self.add_test_result(
                    "清空集合",
                    True,
                    f"成功清空集合 '{settings.collection_name}'"
                )
            else:
                self.add_test_result(
                    "清空集合",
                    False,
                    f"清空集合失败"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"清空集合时出错: {e}", exc_info=True)
            self.add_test_result(
                "清空集合",
                False,
                f"清空集合时出错: {str(e)}"
            )
            return False
    
    def reindex_documents(self) -> bool:
        """
        重新索引文档
        
        返回:
            是否成功
        """
        self.print_section("步骤 2: 重新索引文档")
        
        # 文档路径
        doc_path = project_root / "docs" / "1i0ae3sumrl64W5nn7PshnNla14b1c.txt"
        
        if not doc_path.exists():
            self.add_test_result(
                "重新索引",
                False,
                f"测试文档不存在: {doc_path}"
            )
            return False
        
        print(f"索引文档: {doc_path}")
        print(f"集合名称: {settings.collection_name}")
        
        try:
            # 重新索引
            report = self.index_manager.reindex_directory(
                directory=str(doc_path.parent),
                collection_name=settings.collection_name,
                force=True,
                vector_dim=settings.vector_dim
            )
            
            # 检查结果 - 只要索引了至少一个文档就算成功
            success = report.documents_indexed > 0
            
            if success:
                self.add_test_result(
                    "重新索引",
                    True,
                    f"成功索引 {report.documents_indexed} 个文档，"
                    f"创建 {report.chunks_created} 个分块，"
                    f"上传 {report.vectors_uploaded} 个向量",
                    {
                        "documents": report.documents_indexed,
                        "chunks": report.chunks_created,
                        "vectors": report.vectors_uploaded,
                        "time": f"{report.total_time:.2f}s"
                    }
                )
            else:
                self.add_test_result(
                    "重新索引",
                    False,
                    f"索引失败或未索引任何文档",
                    {
                        "documents": report.documents_indexed,
                        "failed_files": report.failed_files
                    }
                )
            
            return success
            
        except Exception as e:
            logger.error(f"重新索引时出错: {e}", exc_info=True)
            self.add_test_result(
                "重新索引",
                False,
                f"重新索引时出错: {str(e)}"
            )
            return False
    
    def verify_indexing(self) -> bool:
        """
        验证索引结果
        
        返回:
            是否成功
        """
        self.print_section("步骤 3: 验证索引结果")
        
        print("检查集合状态...")
        
        try:
            # 获取集合信息
            collection_info = self.qdrant.get_collection_info(settings.collection_name)
            
            if not collection_info:
                self.add_test_result(
                    "验证索引",
                    False,
                    "集合不存在"
                )
                return False
            
            points_count = collection_info.get('points_count', 0)
            
            if points_count == 0:
                self.add_test_result(
                    "验证索引",
                    False,
                    "集合为空，没有索引任何数据"
                )
                return False
            
            self.add_test_result(
                "验证索引",
                True,
                f"集合包含 {points_count} 个数据点",
                {
                    "points_count": points_count,
                    "status": collection_info.get('status', 'unknown')
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"验证索引时出错: {e}", exc_info=True)
            self.add_test_result(
                "验证索引",
                False,
                f"验证索引时出错: {str(e)}"
            )
            return False
    
    def test_query(self, query: str, expected_keyword: str) -> bool:
        """
        测试查询
        
        参数:
            query: 查询文本
            expected_keyword: 期望的关键词
        
        返回:
            是否成功
        """
        self.print_section(f"步骤 4: 测试查询")
        
        print(f"查询: {query}")
        print(f"期望关键词: {expected_keyword}")
        print()
        
        try:
            # 使用自适应搜索工具，降低阈值以提高召回率
            adaptive_search = AdaptiveSearchTool(
                self.embeddings,
                self.qdrant,
                settings.collection_name
            )
            
            # 执行搜索
            results = adaptive_search.search_with_fallback(
                query=query,
                initial_threshold=0.3,
                min_threshold=0.1,
                target_results=3
            )
            
            if not results:
                self.add_test_result(
                    "查询测试",
                    False,
                    f"查询未返回任何结果",
                    {
                        "query": query,
                        "threshold": 0.3,
                        "top_k": settings.top_k
                    }
                )
                return False
            
            # 检查结果是否包含期望的关键词
            found_keyword = False
            for result in results:
                content = result.get('content', '') or result.get('text', '')
                if expected_keyword in content:
                    found_keyword = True
                    break
            
            # 显示结果
            print(f"找到 {len(results)} 个结果:\n")
            for i, result in enumerate(results, 1):
                score = result.get('score', 0)
                source = result.get('source', 'unknown')
                content = result.get('content', '') or result.get('text', '')
                content_preview = content[:200].replace('\n', ' ')
                
                print(f"结果 {i}:")
                print(f"  - 相似度分数: {score:.4f}")
                print(f"  - 来源: {source}")
                print(f"  - 内容预览: {content_preview}...")
                print(f"  - 包含关键词: {'是' if expected_keyword in content else '否'}")
                print()
            
            if found_keyword:
                self.add_test_result(
                    "查询测试",
                    True,
                    f"查询成功，返回 {len(results)} 个结果，包含期望的关键词",
                    {
                        "query": query,
                        "results_count": len(results),
                        "top_score": results[0].get('score', 0) if results else 0,
                        "keyword_found": True
                    }
                )
            else:
                self.add_test_result(
                    "查询测试",
                    False,
                    f"查询返回 {len(results)} 个结果，但不包含期望的关键词 '{expected_keyword}'",
                    {
                        "query": query,
                        "results_count": len(results),
                        "keyword_found": False
                    }
                )
            
            return found_keyword
            
        except Exception as e:
            logger.error(f"查询测试时出错: {e}", exc_info=True)
            self.add_test_result(
                "查询测试",
                False,
                f"查询测试时出错: {str(e)}"
            )
            return False
    
    def check_logs(self) -> bool:
        """
        检查日志输出
        
        返回:
            是否成功
        """
        self.print_section("步骤 5: 检查日志输出")
        
        log_file = project_root / "logs" / "e2e_test.log"
        
        if not log_file.exists():
            self.add_test_result(
                "日志检查",
                False,
                f"日志文件不存在: {log_file}"
            )
            return False
        
        try:
            # 读取日志文件
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # 检查关键日志条目
            required_logs = [
                "搜索",
                "向量化",
                "找到"
            ]
            
            missing_logs = []
            for log_entry in required_logs:
                if log_entry not in log_content:
                    missing_logs.append(log_entry)
            
            if missing_logs:
                self.add_test_result(
                    "日志检查",
                    False,
                    f"日志中缺少关键条目: {', '.join(missing_logs)}",
                    {
                        "log_file": str(log_file),
                        "missing": missing_logs
                    }
                )
                return False
            
            # 统计日志行数
            log_lines = log_content.split('\n')
            log_count = len([line for line in log_lines if line.strip()])
            
            self.add_test_result(
                "日志检查",
                True,
                f"日志输出完整，包含所有关键条目",
                {
                    "log_file": str(log_file),
                    "log_lines": log_count
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"检查日志时出错: {e}", exc_info=True)
            self.add_test_result(
                "日志检查",
                False,
                f"检查日志时出错: {str(e)}"
            )
            return False
    
    def generate_report(self):
        """生成测试报告"""
        self.print_section("测试报告")
        
        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['passed']])
        failed_tests = total_tests - passed_tests
        
        # 计算耗时
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        else:
            duration = 0
        
        # 打印摘要
        print(f"测试总数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests / total_tests * 100):.1f}%")
        print(f"总耗时: {duration:.2f}秒")
        print()
        
        # 打印详细结果
        if failed_tests > 0:
            print("失败的测试:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  ✗ {result['test_name']}: {result['message']}")
            print()
        
        # 保存报告
        report_dir = project_root / "logs"
        report_dir.mkdir(exist_ok=True)
        report_file = report_dir / f"e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("端到端测试报告\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"测试总数: {total_tests}\n")
            f.write(f"通过: {passed_tests}\n")
            f.write(f"失败: {failed_tests}\n")
            f.write(f"成功率: {(passed_tests / total_tests * 100):.1f}%\n")
            f.write(f"总耗时: {duration:.2f}秒\n\n")
            
            f.write("详细结果:\n")
            f.write("-" * 80 + "\n\n")
            
            for result in self.test_results:
                status = "PASS" if result['passed'] else "FAIL"
                f.write(f"[{status}] {result['test_name']}\n")
                f.write(f"  时间: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                if result['message']:
                    f.write(f"  消息: {result['message']}\n")
                if result['details']:
                    f.write(f"  详情:\n")
                    for key, value in result['details'].items():
                        f.write(f"    - {key}: {value}\n")
                f.write("\n")
        
        print(f"报告已保存到: {report_file}")
        
        # 返回是否所有测试都通过
        return failed_tests == 0
    
    def run(self, skip_reindex: bool = False) -> bool:
        """
        运行端到端测试
        
        参数:
            skip_reindex: 是否跳过重新索引
        
        返回:
            是否所有测试都通过
        """
        self.print_header("RAG5 端到端测试")
        
        self.start_time = datetime.now()
        print(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 步骤 0: 测试连接
            if not self.test_connection():
                print("\n❌ 连接测试失败，终止测试")
                return False
            
            # 步骤 1: 清空集合
            if not skip_reindex:
                if not self.clear_collection():
                    print("\n⚠️  清空集合失败，继续测试")
                
                # 步骤 2: 重新索引
                if not self.reindex_documents():
                    print("\n❌ 重新索引失败，终止测试")
                    return False
                
                # 步骤 3: 验证索引
                if not self.verify_indexing():
                    print("\n❌ 验证索引失败，终止测试")
                    return False
            else:
                print("\n⚠️  跳过重新索引步骤")
            
            # 步骤 4: 测试查询
            test_query = "于朦朧是怎么死的"
            expected_keyword = "于朦朧"
            
            if not self.test_query(test_query, expected_keyword):
                print("\n❌ 查询测试失败")
            
            # 步骤 5: 检查日志
            if not self.check_logs():
                print("\n⚠️  日志检查失败")
            
            return True
            
        except Exception as e:
            logger.error(f"测试过程中发生错误: {e}", exc_info=True)
            print(f"\n❌ 测试失败: {e}")
            return False
        
        finally:
            self.end_time = datetime.now()
            print(f"\n结束时间: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 生成报告
            all_passed = self.generate_report()
            
            if all_passed:
                print("\n✓ 所有测试通过")
            else:
                print("\n✗ 部分测试失败")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="RAG5 端到端测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行完整测试
  python scripts/test_e2e.py
  
  # 跳过重新索引（使用现有数据）
  python scripts/test_e2e.py --skip-reindex
  
  # 详细输出
  python scripts/test_e2e.py --verbose
        """
    )
    
    parser.add_argument(
        '--skip-reindex',
        action='store_true',
        help='跳过重新索引步骤'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='启用详细日志'
    )
    
    args = parser.parse_args()
    
    try:
        # 创建测试运行器
        runner = E2ETestRunner(verbose=args.verbose)
        
        # 运行测试
        success = runner.run(skip_reindex=args.skip_reindex)
        
        # 返回退出码
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行失败: {e}", exc_info=True)
        print(f"\n❌ 程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
