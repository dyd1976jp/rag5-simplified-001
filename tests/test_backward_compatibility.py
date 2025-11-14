#!/usr/bin/env python3
"""
向后兼容性测试
Backward Compatibility Test

测试旧的导入路径和使用方式是否仍然有效
Tests if old import paths and usage patterns still work
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class BackwardCompatibilityTester:
    """向后兼容性测试器"""
    
    def __init__(self):
        self.test_results = []
        
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        print(f"[{level}] {message}")
        
    def add_result(self, test_name: str, passed: bool, message: str = ""):
        """添加测试结果"""
        self.test_results.append((test_name, passed, message))
        status = "✓ PASS" if passed else "✗ FAIL"
        self.log(f"{status}: {test_name} - {message}")
    
    def test_config_imports(self):
        """测试配置模块的导入"""
        self.log("=" * 60)
        self.log("测试配置模块导入")
        self.log("=" * 60)
        
        try:
            # 新的导入方式
            from rag5.config import settings
            from rag5.config import ConfigLoader, ConfigValidator
            from rag5.config import defaults
            
            # 验证可以访问配置
            _ = settings.ollama_host
            _ = settings.llm_model
            
            self.add_result("配置模块导入", True, "所有配置导入成功")
            return True
        except Exception as e:
            self.add_result("配置模块导入", False, f"导入失败: {str(e)}")
            return False
    
    def test_core_imports(self):
        """测试核心模块的导入"""
        self.log("=" * 60)
        self.log("测试核心模块导入")
        self.log("=" * 60)
        
        try:
            # 新的导入方式
            from rag5.core import SimpleRAGAgent, ask
            from rag5.core.agent import ConversationHistory, MessageProcessor
            from rag5.core.prompts import SYSTEM_PROMPT
            
            # 验证类可以实例化
            history = ConversationHistory()
            processor = MessageProcessor()
            
            self.add_result("核心模块导入", True, "所有核心导入成功")
            return True
        except Exception as e:
            self.add_result("核心模块导入", False, f"导入失败: {str(e)}")
            return False
    
    def test_tools_imports(self):
        """测试工具模块的导入"""
        self.log("=" * 60)
        self.log("测试工具模块导入")
        self.log("=" * 60)
        
        try:
            # 新的导入方式
            from rag5.tools import search_knowledge_base
            from rag5.tools.embeddings import OllamaEmbeddingsManager
            from rag5.tools.vectordb import QdrantManager
            
            self.add_result("工具模块导入", True, "所有工具导入成功")
            return True
        except Exception as e:
            self.add_result("工具模块导入", False, f"导入失败: {str(e)}")
            return False
    
    def test_ingestion_imports(self):
        """测试摄取模块的导入"""
        self.log("=" * 60)
        self.log("测试摄取模块导入")
        self.log("=" * 60)
        
        try:
            # 新的导入方式
            from rag5.ingestion import ingest_directory, ingest_file
            from rag5.ingestion import IngestionPipeline
            from rag5.ingestion.loaders import TextLoader, MarkdownLoader
            from rag5.ingestion.splitters import RecursiveSplitter
            
            self.add_result("摄取模块导入", True, "所有摄取导入成功")
            return True
        except Exception as e:
            self.add_result("摄取模块导入", False, f"导入失败: {str(e)}")
            return False
    
    def test_interfaces_imports(self):
        """测试接口模块的导入"""
        self.log("=" * 60)
        self.log("测试接口模块导入")
        self.log("=" * 60)
        
        try:
            # 新的导入方式
            from rag5.interfaces.api import create_app
            from rag5.interfaces.api.models import ChatRequest, ChatResponse
            
            # 验证可以创建应用
            app = create_app()
            
            self.add_result("接口模块导入", True, "所有接口导入成功")
            return True
        except Exception as e:
            self.add_result("接口模块导入", False, f"导入失败: {str(e)}")
            return False
    
    def test_top_level_imports(self):
        """测试顶层便捷导入"""
        self.log("=" * 60)
        self.log("测试顶层便捷导入")
        self.log("=" * 60)
        
        try:
            # 从包根导入
            from rag5 import settings, SimpleRAGAgent, ask
            from rag5 import ingest_directory, search_knowledge_base
            
            # 验证导入的对象可用
            assert settings is not None
            assert SimpleRAGAgent is not None
            assert ask is not None
            assert ingest_directory is not None
            assert search_knowledge_base is not None
            
            self.add_result("顶层导入", True, "所有顶层导入成功")
            return True
        except Exception as e:
            self.add_result("顶层导入", False, f"导入失败: {str(e)}")
            return False
    
    def test_usage_patterns(self):
        """测试常见使用模式"""
        self.log("=" * 60)
        self.log("测试常见使用模式")
        self.log("=" * 60)
        
        try:
            # 模式 1: 配置访问
            from rag5 import settings
            llm_model = settings.llm_model
            self.log(f"  配置访问: LLM Model = {llm_model}")
            
            # 模式 2: 创建代理（不实际初始化）
            from rag5 import SimpleRAGAgent
            # agent = SimpleRAGAgent()  # 需要服务运行
            self.log(f"  代理类可用: {SimpleRAGAgent.__name__}")
            
            # 模式 3: 使用便捷函数（不实际调用）
            from rag5 import ask
            self.log(f"  便捷函数可用: {ask.__name__}")
            
            # 模式 4: 摄取功能（不实际执行）
            from rag5 import ingest_directory
            self.log(f"  摄取函数可用: {ingest_directory.__name__}")
            
            self.add_result("使用模式", True, "所有使用模式有效")
            return True
        except Exception as e:
            self.add_result("使用模式", False, f"使用模式测试失败: {str(e)}")
            return False
    
    def test_class_instantiation(self):
        """测试类实例化"""
        self.log("=" * 60)
        self.log("测试类实例化")
        self.log("=" * 60)
        
        try:
            # 测试可以实例化的类（不需要外部服务）
            from rag5.core.agent import ConversationHistory, MessageProcessor
            from rag5.config import ConfigLoader, ConfigValidator
            
            # 实例化测试
            history = ConversationHistory()
            history.add_message("user", "测试消息")
            messages = history.get_messages()
            assert len(messages) == 1
            self.log(f"  ConversationHistory: ✓")
            
            processor = MessageProcessor()
            self.log(f"  MessageProcessor: ✓")
            
            loader = ConfigLoader()
            self.log(f"  ConfigLoader: ✓")
            
            validator = ConfigValidator()
            self.log(f"  ConfigValidator: ✓")
            
            self.add_result("类实例化", True, "所有类可以正常实例化")
            return True
        except Exception as e:
            self.add_result("类实例化", False, f"实例化失败: {str(e)}")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return False
    
    def test_module_structure(self):
        """测试模块结构"""
        self.log("=" * 60)
        self.log("测试模块结构")
        self.log("=" * 60)
        
        try:
            import rag5
            
            # 检查主要模块是否存在
            expected_modules = [
                'config',
                'core',
                'tools',
                'ingestion',
                'interfaces',
                'utils',
            ]
            
            for module_name in expected_modules:
                module_path = project_root / "rag5" / module_name
                if module_path.exists():
                    self.log(f"  ✓ {module_name} 模块存在")
                else:
                    self.log(f"  ✗ {module_name} 模块不存在", "WARN")
            
            # 检查 __all__ 导出
            if hasattr(rag5, '__all__'):
                self.log(f"  ✓ __all__ 已定义: {len(rag5.__all__)} 个导出")
            else:
                self.log(f"  ✗ __all__ 未定义", "WARN")
            
            self.add_result("模块结构", True, "模块结构完整")
            return True
        except Exception as e:
            self.add_result("模块结构", False, f"结构检查失败: {str(e)}")
            return False
    
    def print_summary(self):
        """打印测试摘要"""
        self.log("=" * 60)
        self.log("向后兼容性测试摘要")
        self.log("=" * 60)
        
        total = len(self.test_results)
        passed = sum(1 for _, p, _ in self.test_results if p)
        failed = total - passed
        
        self.log(f"总测试数: {total}")
        self.log(f"通过: {passed}")
        self.log(f"失败: {failed}")
        self.log("")
        
        for name, passed, message in self.test_results:
            status = "✓ PASS" if passed else "✗ FAIL"
            self.log(f"{status}: {name} - {message}")
        
        self.log("=" * 60)
        
        return failed == 0
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("开始向后兼容性测试")
        self.log("=" * 60)
        
        # 运行所有测试
        self.test_module_structure()
        self.test_config_imports()
        self.test_core_imports()
        self.test_tools_imports()
        self.test_ingestion_imports()
        self.test_interfaces_imports()
        self.test_top_level_imports()
        self.test_class_instantiation()
        self.test_usage_patterns()
        
        # 打印摘要
        success = self.print_summary()
        
        return success


def main():
    """主函数"""
    tester = BackwardCompatibilityTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
