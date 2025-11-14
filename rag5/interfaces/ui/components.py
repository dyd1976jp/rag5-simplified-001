"""
Streamlit UI 组件。

本模块定义了可重用的 UI 组件，用于构建聊天界面。
"""

import streamlit as st
import requests
from typing import List, Dict
import logging

from rag5.config.settings import settings

logger = logging.getLogger(__name__)


def render_page_header():
    """
    渲染页面标题和描述。

    Example:
        >>> render_page_header()
    """
    st.title("🤖 Simple RAG")
    st.markdown("""
    欢迎使用简化版 RAG 系统！您可以向我提问，我会从知识库中搜索相关信息来回答您的问题。
    """)


def render_message(message: Dict[str, str]):
    """
    渲染单条消息。

    Args:
        message: 包含 role 和 content 的消息字典

    Example:
        >>> message = {"role": "user", "content": "什么是 RAG？"}
        >>> render_message(message)
    """
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def render_chat_history(messages: List[Dict[str, str]]):
    """
    渲染对话历史。

    Args:
        messages: 消息列表

    Example:
        >>> messages = [
        ...     {"role": "user", "content": "你好"},
        ...     {"role": "assistant", "content": "你好！有什么可以帮助你的？"}
        ... ]
        >>> render_chat_history(messages)
    """
    for message in messages:
        render_message(message)


def render_error(error: str):
    """
    渲染错误消息。

    Args:
        error: 错误消息字符串

    Example:
        >>> render_error("连接失败")
    """
    if error:
        st.error(error)


def render_sidebar_settings():
    """
    渲染侧边栏设置部分。

    Returns:
        如果用户点击了清空对话按钮，返回 True

    Example:
        >>> if render_sidebar_settings():
        ...     # 清空对话逻辑
    """
    st.header("⚙️ 设置")

    # 清空对话按钮
    clear_clicked = st.button("清空对话", use_container_width=True)

    return clear_clicked


def render_sidebar_info(turn_count: int, message_count: int):
    """
    渲染侧边栏系统信息。

    Args:
        turn_count: 对话轮数
        message_count: 消息总数

    Example:
        >>> render_sidebar_info(turn_count=5, message_count=10)
    """
    st.divider()
    st.subheader("📊 系统信息")
    st.metric("对话轮数", turn_count)
    st.metric("消息总数", message_count)


def render_sidebar_limits():
    """
    渲染侧边栏限制信息。

    Example:
        >>> render_sidebar_limits()
    """
    st.divider()
    st.subheader("📏 限制")
    st.text(f"最大问题长度: {settings.max_query_length}")
    st.text(f"历史消息限制: 20 条")


def render_sidebar_status():
    """
    渲染侧边栏系统状态。

    检查 Ollama 和 Qdrant 服务的可用性并显示状态。

    Example:
        >>> render_sidebar_status()
    """
    st.divider()
    st.subheader("🔧 系统状态")

    try:
        # 检查 Ollama
        try:
            response = requests.get(
                f"{settings.ollama_host}/api/tags",
                timeout=2
            )
            if response.status_code == 200:
                st.success("Ollama: ✓ 运行中")
            else:
                st.error("Ollama: ✗ 错误")
        except Exception as e:
            logger.warning(f"Ollama status check failed: {e}")
            st.error("Ollama: ✗ 未连接")

        # 检查 Qdrant
        try:
            response = requests.get(
                f"{settings.qdrant_url}/collections",
                timeout=2
            )
            if response.status_code == 200:
                st.success("Qdrant: ✓ 运行中")
            else:
                st.error("Qdrant: ✗ 错误")
        except Exception as e:
            logger.warning(f"Qdrant status check failed: {e}")
            st.error("Qdrant: ✗ 未连接")

    except Exception as e:
        logger.error(f"Status check error: {e}")
        st.error(f"状态检查失败: {e}")


def render_sidebar(turn_count: int, message_count: int):
    """
    渲染完整的侧边栏。

    Args:
        turn_count: 对话轮数
        message_count: 消息总数

    Returns:
        如果用户点击了清空对话按钮，返回 True

    Example:
        >>> if render_sidebar(turn_count=5, message_count=10):
        ...     # 清空对话逻辑
    """
    with st.sidebar:
        clear_clicked = render_sidebar_settings()
        render_sidebar_info(turn_count, message_count)
        render_sidebar_limits()
        render_sidebar_status()

    return clear_clicked
