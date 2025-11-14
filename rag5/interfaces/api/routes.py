"""
API 路由定义。

本模块定义了所有 API 端点的路由，将 HTTP 请求映射到处理器。
"""

from fastapi import APIRouter
from .models import ChatRequest, ChatResponse, ErrorResponse, HealthResponse
from .handlers import ChatHandler, HealthHandler

# 创建 API 路由器
router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
        504: {"model": ErrorResponse, "description": "Request timeout"}
    },
    summary="Chat with the RAG agent",
    description="Send a query to the RAG agent and receive an answer based on the knowledge base"
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    聊天端点，处理用户查询并返回答案。

    Args:
        request: ChatRequest 对象，包含查询和可选的历史记录

    Returns:
        ChatResponse 对象，包含生成的答案

    Raises:
        HTTPException: 当请求无效或处理失败时
    """
    return await ChatHandler.handle_chat(request)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the system and its components"
)
async def health() -> HealthResponse:
    """
    健康检查端点。

    Returns:
        HealthResponse 对象，包含系统状态和各组件状态
    """
    return await HealthHandler.handle_health()
