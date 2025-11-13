"""
API 请求和响应模型定义。

本模块定义了 FastAPI 使用的 Pydantic 模型，包括请求验证和响应格式。
"""

from typing import List, Optional
from pydantic import BaseModel, Field, validator


class Message(BaseModel):
    """
    消息模型，用于对话历史。

    Attributes:
        role: 消息发送者的角色（user 或 assistant）
        content: 消息内容
    """
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")

    @validator('role')
    def validate_role(cls, v):
        """验证角色必须是 user 或 assistant"""
        if v not in ['user', 'assistant']:
            raise ValueError('Role must be either "user" or "assistant"')
        return v

    @validator('content')
    def validate_content(cls, v):
        """验证内容不能为空且不超过最大长度"""
        from rag5.config.settings import settings

        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v) > settings.max_query_length:
            raise ValueError(f'Content exceeds maximum length of {settings.max_query_length} characters')
        return v.strip()


class ChatRequest(BaseModel):
    """
    聊天请求模型。

    Attributes:
        query: 用户查询
        history: 可选的对话历史
    """
    query: str = Field(..., description="User query", min_length=1)
    history: Optional[List[Message]] = Field(default=[], description="Optional chat history")

    @validator('query')
    def validate_query(cls, v):
        """验证查询不能为空且不超过最大长度"""
        from rag5.config.settings import settings

        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        if len(v) > settings.max_query_length:
            raise ValueError(f'Query exceeds maximum length of {settings.max_query_length} characters')
        return v.strip()

    @validator('history')
    def validate_history(cls, v):
        """验证历史消息数量不超过限制"""
        if v and len(v) > 50:
            raise ValueError('History cannot exceed 50 messages')
        return v


class ChatResponse(BaseModel):
    """
    聊天响应模型。

    Attributes:
        answer: 代理生成的答案
    """
    answer: str = Field(..., description="Generated answer from the agent")


class ErrorResponse(BaseModel):
    """
    错误响应模型。

    Attributes:
        detail: 错误消息
    """
    detail: str = Field(..., description="Error message")


class HealthResponse(BaseModel):
    """
    健康检查响应模型。

    Attributes:
        status: 整体状态（ok, degraded, error）
        components: 各组件的状态
    """
    status: str = Field(..., description="Overall system status")
    components: dict = Field(default_factory=dict, description="Status of individual components")
