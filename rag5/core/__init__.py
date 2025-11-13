"""
核心模块

导出代理和提示词相关的所有组件。
"""

# 代理组件
from rag5.core.agent import (
    SimpleRAGAgent,
    ask,
    AgentInitializer,
    MessageProcessor,
    ConversationHistory,
    ErrorHandler,
    RetryHandler,
    TimeoutError,
    retry_with_backoff
)

# 提示词
from rag5.core.prompts import (
    SYSTEM_PROMPT,
    SEARCH_TOOL_DESCRIPTION,
    TOOL_DESCRIPTION
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

    # 提示词
    'SYSTEM_PROMPT',
    'SEARCH_TOOL_DESCRIPTION',
    'TOOL_DESCRIPTION',
]
