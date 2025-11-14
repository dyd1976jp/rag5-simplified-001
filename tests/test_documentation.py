#!/usr/bin/env python3
"""
文档验证测试
Documentation Validation Test

验证所有文档的完整性和准确性
Validates completeness and accuracy of all documentation
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple, Dict

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DocumentationValidator:
    """文档验证器"""
    
    def __init__(self):
        self.test_results = []
        self.issues = []
        
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        print(f"[{level}] {message}")
        
    def add_result(self, test_name: str, passed: bool, message: str = ""):
        """添加测试结果"""
        self.test_results.append((test_name, passed, message))
        status = "✓ PASS" if passed else "✗ FAIL"
        self.log(f"{status}: {test_name} - {message}")
    
    def add_issue(self, file_path: str, issue: str):
        """添加问题"""
        self.issues.append((file_path, issue))
        self.log(f"  ⚠ {file_path}: {issue}", "WARN")
    
    def check_file_exists(self, file_path: Path) -> bool:
        """检查文件是否存在"""
        return file_path.exists() and file_path.is_file()
    
    def check_readme_structure(self, readme_path: Path) -> Tuple[bool, List[str]]:
        """检查 README 文件结构"""
        if not self.check_file_exists(readme_path):
            return False, ["文件不存在"]
        
        content = readme_path.read_text(encoding="utf-8")
        issues = []
        
        # 检查必要的章节
        required_sections = [
            r"#.*特性|#.*Features",
            r"#.*安装|#.*Installation|#.*快速开始|#.*Quick Start",
            r"#.*使用|#.*Usage",
        ]
        
        for pattern in required_sections:
            if not re.search(pattern, content, re.IGNORECASE):
                issues.append(f"缺少章节: {pattern}")
        
        # 检查代码示例
        code_blocks = re.findall(r"```[\s\S]*?```", content)
        if len(code_blocks) == 0:
            issues.append("缺少代码示例")
        
        return len(issues) == 0, issues
    
    def check_code_examples(self, readme_path: Path) -> Tuple[bool, List[str]]:
        """检查代码示例的有效性"""
        if not self.check_file_exists(readme_path):
            return False, ["文件不存在"]
        
        content = readme_path.read_text(encoding="utf-8")
        issues = []
        
        # 提取 Python 代码块
        python_blocks = re.findall(r"```python\n([\s\S]*?)```", content)
        
        for i, code in enumerate(python_blocks):
            # 检查导入语句
            if "from rag5" in code or "import rag5" in code:
                # 验证导入路径
                imports = re.findall(r"from rag5[.\w]* import [\w, ]+", code)
                for imp in imports:
                    # 简单的语法检查
                    if not re.match(r"from rag5(\.\w+)* import \w+(, \w+)*", imp):
                        issues.append(f"代码块 {i+1}: 可能的导入错误: {imp}")
        
        return len(issues) == 0, issues
    
    def test_main_readme(self):
        """测试主 README"""
        self.log("=" * 60)
        self.log("测试主 README.md")
        self.log("=" * 60)
        
        readme_path = project_root / "README.md"
        
        # 检查文件存在
        if not self.check_file_exists(readme_path):
            self.add_result("主 README", False, "文件不存在")
            return False
        
        # 检查结构
        structure_ok, structure_issues = self.check_readme_structure(readme_path)
        if not structure_ok:
            for issue in structure_issues:
                self.add_issue(str(readme_path), issue)
        
        # 检查代码示例
        examples_ok, example_issues = self.check_code_examples(readme_path)
        if not examples_ok:
            for issue in example_issues:
                self.add_issue(str(readme_path), issue)
        
        # 检查中文内容
        content = readme_path.read_text(encoding="utf-8")
        has_chinese = bool(re.search(r"[\u4e00-\u9fff]", content))
        if not has_chinese:
            self.add_issue(str(readme_path), "缺少中文内容")
        
        if structure_ok and examples_ok and has_chinese:
            self.add_result("主 README", True, "文档完整且有效")
            return True
        else:
            self.add_result("主 README", False, f"发现 {len(structure_issues) + len(example_issues)} 个问题")
            return False
    
    def test_module_readmes(self):
        """测试模块 README"""
        self.log("=" * 60)
        self.log("测试模块 README 文件")
        self.log("=" * 60)
        
        # 需要 README 的模块
        modules_with_readme = [
            "rag5/config",
            "rag5/core",
            "rag5/tools",
            "rag5/ingestion",
            "rag5/interfaces",
            "scripts",
        ]
        
        all_ok = True
        for module_path in modules_with_readme:
            readme_path = project_root / module_path / "README.md"
            
            if not self.check_file_exists(readme_path):
                self.add_issue(module_path, "README.md 不存在")
                all_ok = False
                continue
            
            # 检查基本结构
            content = readme_path.read_text(encoding="utf-8")
            
            # 检查是否有标题
            if not re.search(r"^#\s+", content, re.MULTILINE):
                self.add_issue(str(readme_path), "缺少标题")
                all_ok = False
            
            # 检查是否有中文
            if not re.search(r"[\u4e00-\u9fff]", content):
                self.add_issue(str(readme_path), "缺少中文内容")
                all_ok = False
            
            # 检查是否有功能说明
            if len(content) < 100:
                self.add_issue(str(readme_path), "内容过短，可能缺少详细说明")
                all_ok = False
            
            self.log(f"  ✓ {module_path}/README.md")
        
        if all_ok:
            self.add_result("模块 README", True, f"所有 {len(modules_with_readme)} 个模块 README 完整")
            return True
        else:
            self.add_result("模块 README", False, "部分模块 README 有问题")
            return False
    
    def test_docstrings(self):
        """测试代码文档字符串"""
        self.log("=" * 60)
        self.log("测试代码 Docstrings")
        self.log("=" * 60)
        
        # 检查主要模块的 docstrings
        modules_to_check = [
            "rag5/config/settings.py",
            "rag5/core/agent/agent.py",
            "rag5/tools/search/search_tool.py",
            "rag5/ingestion/pipeline.py",
            "rag5/interfaces/api/app.py",
        ]
        
        all_ok = True
        for module_path in modules_to_check:
            file_path = project_root / module_path
            
            if not self.check_file_exists(file_path):
                self.add_issue(module_path, "文件不存在")
                all_ok = False
                continue
            
            content = file_path.read_text(encoding="utf-8")
            
            # 检查模块级 docstring
            if not re.search(r'^"""[\s\S]*?"""', content, re.MULTILINE):
                self.add_issue(module_path, "缺少模块级 docstring")
                all_ok = False
            
            # 检查类和函数的 docstring
            classes = re.findall(r"^class\s+(\w+)", content, re.MULTILINE)
            functions = re.findall(r"^def\s+(\w+)", content, re.MULTILINE)
            
            # 检查是否有中文 docstring
            has_chinese_docs = bool(re.search(r'"""[\s\S]*?[\u4e00-\u9fff][\s\S]*?"""', content))
            if not has_chinese_docs and (classes or functions):
                self.add_issue(module_path, "缺少中文 docstring")
                all_ok = False
            
            self.log(f"  ✓ {module_path}: {len(classes)} 个类, {len(functions)} 个函数")
        
        if all_ok:
            self.add_result("代码 Docstrings", True, "主要模块都有适当的文档")
            return True
        else:
            self.add_result("代码 Docstrings", False, "部分模块缺少文档")
            return False
    
    def test_example_code_validity(self):
        """测试示例代码的有效性"""
        self.log("=" * 60)
        self.log("测试示例代码有效性")
        self.log("=" * 60)
        
        readme_path = project_root / "README.md"
        
        if not self.check_file_exists(readme_path):
            self.add_result("示例代码", False, "README 不存在")
            return False
        
        content = readme_path.read_text(encoding="utf-8")
        
        # 提取 Python 代码示例
        python_examples = re.findall(r"```python\n([\s\S]*?)```", content)
        
        if len(python_examples) == 0:
            self.add_result("示例代码", False, "未找到 Python 代码示例")
            return False
        
        self.log(f"找到 {len(python_examples)} 个 Python 代码示例")
        
        # 验证导入语句
        valid_imports = 0
        for i, example in enumerate(python_examples):
            if "from rag5" in example or "import rag5" in example:
                # 尝试验证导入
                imports = re.findall(r"from rag5[.\w]* import [\w, ]+", example)
                if imports:
                    self.log(f"  示例 {i+1}: {len(imports)} 个导入语句")
                    valid_imports += 1
        
        if valid_imports > 0:
            self.add_result("示例代码", True, f"{valid_imports} 个示例包含有效的导入语句")
            return True
        else:
            self.add_result("示例代码", False, "示例代码可能缺少导入语句")
            return False
    
    def test_configuration_documentation(self):
        """测试配置文档"""
        self.log("=" * 60)
        self.log("测试配置文档")
        self.log("=" * 60)
        
        # 检查 .env.example
        env_example = project_root / ".env.example"
        if not self.check_file_exists(env_example):
            self.add_issue(".env.example", "文件不存在")
            self.add_result("配置文档", False, ".env.example 不存在")
            return False
        
        # 检查配置 README
        config_readme = project_root / "rag5" / "config" / "README.md"
        if not self.check_file_exists(config_readme):
            self.add_issue("rag5/config/README.md", "文件不存在")
            self.add_result("配置文档", False, "配置 README 不存在")
            return False
        
        # 检查配置项是否在文档中说明
        env_content = env_example.read_text(encoding="utf-8")
        config_doc = config_readme.read_text(encoding="utf-8")
        
        # 提取环境变量
        env_vars = re.findall(r"^([A-Z_]+)=", env_content, re.MULTILINE)
        
        missing_docs = []
        for var in env_vars:
            if var not in config_doc:
                missing_docs.append(var)
        
        if missing_docs:
            self.add_issue("rag5/config/README.md", f"缺少配置项说明: {', '.join(missing_docs)}")
            self.add_result("配置文档", False, f"{len(missing_docs)} 个配置项缺少说明")
            return False
        else:
            self.add_result("配置文档", True, f"所有 {len(env_vars)} 个配置项都有说明")
            return True
    
    def test_chinese_content(self):
        """测试中文内容的质量"""
        self.log("=" * 60)
        self.log("测试中文内容质量")
        self.log("=" * 60)
        
        # 检查主要文档的中文内容
        docs_to_check = [
            project_root / "README.md",
            project_root / "rag5" / "config" / "README.md",
            project_root / "rag5" / "core" / "README.md",
            project_root / "rag5" / "tools" / "README.md",
        ]
        
        all_ok = True
        for doc_path in docs_to_check:
            if not self.check_file_exists(doc_path):
                continue
            
            content = doc_path.read_text(encoding="utf-8")
            
            # 统计中文字符
            chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", content))
            total_chars = len(content)
            
            if chinese_chars == 0:
                self.add_issue(str(doc_path), "没有中文内容")
                all_ok = False
            elif chinese_chars < 100:
                self.add_issue(str(doc_path), f"中文内容较少 ({chinese_chars} 字符)")
                all_ok = False
            else:
                self.log(f"  ✓ {doc_path.name}: {chinese_chars} 个中文字符")
        
        if all_ok:
            self.add_result("中文内容", True, "所有文档都有充足的中文内容")
            return True
        else:
            self.add_result("中文内容", False, "部分文档中文内容不足")
            return False
    
    def print_summary(self):
        """打印测试摘要"""
        self.log("=" * 60)
        self.log("文档验证测试摘要")
        self.log("=" * 60)
        
        total = len(self.test_results)
        passed = sum(1 for _, p, _ in self.test_results if p)
        failed = total - passed
        
        self.log(f"总测试数: {total}")
        self.log(f"通过: {passed}")
        self.log(f"失败: {failed}")
        self.log(f"发现问题: {len(self.issues)}")
        self.log("")
        
        for name, passed, message in self.test_results:
            status = "✓ PASS" if passed else "✗ FAIL"
            self.log(f"{status}: {name} - {message}")
        
        if self.issues:
            self.log("")
            self.log("详细问题列表:")
            for file_path, issue in self.issues:
                self.log(f"  • {file_path}: {issue}")
        
        self.log("=" * 60)
        
        return failed == 0
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("开始文档验证测试")
        self.log("=" * 60)
        
        # 运行所有测试
        self.test_main_readme()
        self.test_module_readmes()
        self.test_docstrings()
        self.test_example_code_validity()
        self.test_configuration_documentation()
        self.test_chinese_content()
        
        # 打印摘要
        success = self.print_summary()
        
        return success


def main():
    """主函数"""
    validator = DocumentationValidator()
    success = validator.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
