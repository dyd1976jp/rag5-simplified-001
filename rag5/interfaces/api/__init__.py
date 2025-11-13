"""
API 接口模块。

本模块提供 REST API 接口，包括请求/响应模型、路由定义和应用创建。

使用示例：
    from rag5.interfaces.api import create_app
    from rag5.interfaces.api.models import ChatRequest, ChatResponse
"""

# 导入主要接口
from .app import create_app
from .models import ChatRequest, ChatResponse, Message
from .kb_routes import kb_router, set_kb_manager

__all__ = [
    'create_app',
    'ChatRequest',
    'ChatResponse',
    'Message',
    'kb_router',
    'set_kb_manager',
]
