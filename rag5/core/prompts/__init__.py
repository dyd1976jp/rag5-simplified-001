"""
提示词模块

导出所有提示词常量供代理使用。
"""

from rag5.core.prompts.system import SYSTEM_PROMPT, KNOWLEDGEBASE_TOOL_PROMPT
from rag5.core.prompts.tools import (
    SEARCH_TOOL_DESCRIPTION,
    TOOL_DESCRIPTION
)

__all__ = [
    'SYSTEM_PROMPT',
    'KNOWLEDGEBASE_TOOL_PROMPT',
    'SEARCH_TOOL_DESCRIPTION',
    'TOOL_DESCRIPTION',
]
