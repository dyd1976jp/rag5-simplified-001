"""
Streamlit Web UI 应用。

本模块实现了基于 Streamlit 的 Web 用户界面，提供聊天交互和知识库管理功能。
"""

import streamlit as st
import logging

from rag5.interfaces.ui.state import SessionState
from rag5.interfaces.ui.pages.chat import render_chat_page
from rag5.interfaces.ui.pages.knowledge_base.list import render_kb_list_page
from rag5.interfaces.ui.pages.knowledge_base.detail import render_kb_detail_page
from rag5.interfaces.ui.pages.knowledge_base.api_client import KnowledgeBaseAPIClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_page():
    """
    配置 Streamlit 页面。

    设置页面标题、图标和布局。
    """
    st.set_page_config(
        page_title="Simple RAG",
        page_icon="🤖",
        layout="wide"
    )


def render_kb_management():
    """
    渲染知识库管理页面。

    根据当前页面状态显示相应的知识库管理界面。
    """
    # Initialize API client
    api_client = KnowledgeBaseAPIClient()
    
    # Get current KB management page state
    kb_page = st.session_state.get("current_page", "kb_list")
    
    # Route to appropriate page
    if kb_page == "kb_detail":
        render_kb_detail_page(api_client)
    else:
        # Default to list page
        render_kb_list_page(api_client)


def main():
    """
    主应用函数。

    初始化应用并渲染所有组件，支持多页面导航。

    Example:
        >>> if __name__ == "__main__":
        ...     main()
    """
    # 设置页面
    setup_page()

    # 初始化会话状态
    SessionState.initialize()

    # 侧边栏导航
    with st.sidebar:
        st.title("🧭 导航")
        page = st.radio(
            "选择页面",
            ["💬 聊天", "📚 知识库管理"],
            key="navigation",
            label_visibility="collapsed"
        )

        # 更新当前页面状态
        if page == "💬 聊天":
            SessionState.set_current_page("chat")
        else:
            SessionState.set_current_page("kb_management")

    # 根据选择的页面渲染相应内容
    current_page = SessionState.get_current_page()

    if current_page == "chat" or page == "💬 聊天":
        render_chat_page()
    else:
        render_kb_management()


if __name__ == "__main__":
    main()
