"""
接口模块

提供 REST API 和 Web UI 接口，用于与 RAG5 系统交互。

注意：API 和 UI 模块需要分别导入，因为它们有不同的依赖。
"""

# 延迟导入以避免依赖问题
# 使用时需要显式导入：
# from rag5.interfaces.api import app
# from rag5.interfaces.ui import main

__all__ = ['api', 'ui']
