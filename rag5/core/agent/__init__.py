"""
代理子模块

导出代理相关的所有组件。
"""

from rag5.core.agent.agent import SimpleRAGAgent, ask
from rag5.core.agent.initializer import AgentInitializer
from rag5.core.agent.messages import MessageProcessor
from rag5.core.agent.history import ConversationHistory
from rag5.core.agent.errors import (
    ErrorHandler,
    RetryHandler,
    TimeoutError,
    retry_with_backoff
)

__all__ = [
    # 主代理
    'SimpleRAGAgent',
    'ask',

    # 初始化
    'AgentInitializer',

    # 消息处理
    'MessageProcessor',

    # 历史管理
    'ConversationHistory',

    # 错误处理
    'ErrorHandler',
    'RetryHandler',
    'TimeoutError',
    'retry_with_backoff',
]
