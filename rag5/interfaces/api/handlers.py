"""
API 请求处理器。

本模块实现了 API 端点的业务逻辑，将路由定义与实际处理分离。
"""

import logging
from typing import Dict, Any
from fastapi import HTTPException, status
import requests

from rag5.core.agent.agent import ask
from rag5.config.settings import settings
from .models import ChatRequest, ChatResponse, HealthResponse

logger = logging.getLogger(__name__)


class ChatHandler:
    """
    聊天请求处理器。

    负责处理聊天请求的业务逻辑，包括输入验证、调用代理和错误处理。
    """

    @staticmethod
    async def handle_chat(request: ChatRequest) -> ChatResponse:
        """
        处理聊天请求。

        Args:
            request: ChatRequest 对象，包含查询和可选的历史记录

        Returns:
            ChatResponse 对象，包含生成的答案

        Raises:
            HTTPException: 当请求无效、服务不可用或处理失败时

        Example:
            >>> request = ChatRequest(query="什么是 RAG？")
            >>> response = await ChatHandler.handle_chat(request)
            >>> print(response.answer)
        """
        try:
            logger.info(f"Received chat request with query: {request.query[:100]}...")

            # 额外的输入验证
            if not request.query or not request.query.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Query cannot be empty"
                )

            # 转换历史记录格式
            history = None
            if request.history:
                history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in request.history
                ]
                logger.debug(f"Converted {len(history)} history messages")

            # 调用代理的 ask 函数
            try:
                answer = ask(request.query, history)
            except ConnectionError as e:
                logger.error(f"Connection error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Service unavailable: {str(e)}"
                )
            except ValueError as e:
                logger.error(f"Configuration error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Configuration error: {str(e)}"
                )

            # 检查响应中是否包含超时信息
            if "超时" in answer or "timeout" in answer.lower():
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Request timed out. Please try again."
                )

            logger.info(f"Generated answer with length: {len(answer)}")

            return ChatResponse(answer=answer)

        except HTTPException:
            # 重新抛出 HTTP 异常
            raise
        except ValueError as e:
            # 验证错误
            logger.error(f"Validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            # 未预期的错误
            logger.error(f"Error processing chat request: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}"
            )


class HealthHandler:
    """
    健康检查处理器。

    负责检查系统各组件的健康状态。
    """

    @staticmethod
    async def handle_health() -> HealthResponse:
        """
        处理健康检查请求。

        检查 Ollama 和 Qdrant 服务的可用性。

        Returns:
            HealthResponse 对象，包含系统状态和各组件状态

        Example:
            >>> response = await HealthHandler.handle_health()
            >>> print(response.status)  # "ok", "degraded", or "error"
        """
        try:
            status_info = {
                "status": "ok",
                "components": {}
            }

            # 检查 Ollama 服务
            try:
                response = requests.get(
                    f"{settings.ollama_host}/api/tags",
                    timeout=2
                )
                status_info["components"]["ollama"] = (
                    "ok" if response.status_code == 200 else "error"
                )
            except Exception as e:
                logger.warning(f"Ollama health check failed: {e}")
                status_info["components"]["ollama"] = "error"

            # 检查 Qdrant 服务
            try:
                response = requests.get(
                    f"{settings.qdrant_url}/collections",
                    timeout=2
                )
                status_info["components"]["qdrant"] = (
                    "ok" if response.status_code == 200 else "error"
                )
            except Exception as e:
                logger.warning(f"Qdrant health check failed: {e}")
                status_info["components"]["qdrant"] = "error"

            # 确定整体状态
            if any(v == "error" for v in status_info["components"].values()):
                status_info["status"] = "degraded"

            return HealthResponse(**status_info)

        except Exception as e:
            logger.error(f"Health check error: {e}")
            return HealthResponse(
                status="error",
                components={"error": str(e)}
            )
