"""
Streamlit 会话状态管理。

本模块负责管理 Streamlit 应用的会话状态，包括对话历史和错误信息。
"""

import streamlit as st
from typing import List, Dict, Optional, Any


class SessionState:
    """
    会话状态管理器。

    封装 Streamlit 的 session_state，提供类型安全的访问接口。
    """

    @staticmethod
    def initialize():
        """
        初始化会话状态。

        如果会话状态中不存在必要的键，则创建它们。

        Example:
            >>> SessionState.initialize()
            >>> messages = SessionState.get_messages()
        """
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "error" not in st.session_state:
            st.session_state.error = None
        if "last_retrieval_context" not in st.session_state:
            st.session_state.last_retrieval_context = {}

    @staticmethod
    def get_messages() -> List[Dict[str, str]]:
        """
        获取对话消息列表。

        Returns:
            消息列表，每条消息包含 role 和 content 字段

        Example:
            >>> messages = SessionState.get_messages()
            >>> for msg in messages:
            ...     print(f"{msg['role']}: {msg['content']}")
        """
        SessionState.initialize()
        return st.session_state.messages

    @staticmethod
    def add_message(role: str, content: str, retrieval_results: Optional[List[Dict[str, Any]]] = None):
        """
        添加一条消息到对话历史。

        Args:
            role: 消息角色（user 或 assistant）
            content: 消息内容
            retrieval_results: 可选的检索结果列表（仅用于 assistant 消息）

        Example:
            >>> SessionState.add_message("user", "什么是 RAG？")
            >>> SessionState.add_message("assistant", "RAG 是检索增强生成...", retrieval_results=[...])
        """
        SessionState.initialize()
        message = {
            "role": role,
            "content": content
        }
        if retrieval_results is not None and role == "assistant":
            message["retrieval_results"] = retrieval_results
        st.session_state.messages.append(message)

    @staticmethod
    def clear_messages():
        """
        清空所有对话消息。

        Example:
            >>> SessionState.clear_messages()
            >>> assert len(SessionState.get_messages()) == 0
        """
        st.session_state.messages = []

    @staticmethod
    def get_error() -> Optional[str]:
        """
        获取当前错误信息。

        Returns:
            错误信息字符串，如果没有错误则返回 None
        """
        SessionState.initialize()
        return st.session_state.error

    @staticmethod
    def set_error(error: Optional[str]):
        """
        设置错误信息。

        Args:
            error: 错误信息字符串，或 None 清除错误

        Example:
            >>> SessionState.set_error("连接失败")
            >>> error = SessionState.get_error()
            >>> print(error)  # "连接失败"
        """
        SessionState.initialize()
        st.session_state.error = error

    @staticmethod
    def clear_error():
        """
        清除错误信息。

        Example:
            >>> SessionState.clear_error()
            >>> assert SessionState.get_error() is None
        """
        st.session_state.error = None

    @staticmethod
    def get_history(limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        获取对话历史（不包括最后一条消息）。

        Args:
            limit: 限制返回的消息数量，None 表示不限制

        Returns:
            历史消息列表

        Example:
            >>> # 获取最近 20 条历史消息
            >>> history = SessionState.get_history(limit=20)
        """
        messages = SessionState.get_messages()

        # 排除最后一条消息（当前查询）
        if len(messages) > 1:
            history = messages[:-1]
        else:
            history = []

        # 应用限制
        if limit and len(history) > limit:
            history = history[-limit:]

        return history

    @staticmethod
    def set_last_retrieval_context(context: Optional[Dict[str, Any]]):
        """
        设置最近一次检索结果上下文。

        Args:
            context: 包含查询、知识库 ID、结果列表等信息的字典
        """
        SessionState.initialize()
        st.session_state.last_retrieval_context = context or {}

    @staticmethod
    def get_last_retrieval_context() -> Dict[str, Any]:
        """
        获取最近一次检索结果上下文。

        Returns:
            字典，包含键: query, kb_id, results, error
        """
        SessionState.initialize()
        return getattr(st.session_state, "last_retrieval_context", {})

    @staticmethod
    def get_turn_count() -> int:
        """
        获取对话轮数。

        Returns:
            对话轮数（消息总数除以 2）

        Example:
            >>> turn_count = SessionState.get_turn_count()
            >>> print(f"已进行 {turn_count} 轮对话")
        """
        return len(SessionState.get_messages()) // 2

    @staticmethod
    def get_current_page() -> str:
        """
        获取当前页面。

        Returns:
            当前页面标识符，默认为 "chat"

        Example:
            >>> page = SessionState.get_current_page()
            >>> print(f"当前页面: {page}")
        """
        if "current_page" not in st.session_state:
            st.session_state.current_page = "chat"
        return st.session_state.current_page

    @staticmethod
    def set_current_page(page: str):
        """
        设置当前页面。

        Args:
            page: 页面标识符（如 "chat", "kb_list", "kb_detail"）

        Example:
            >>> SessionState.set_current_page("kb_list")
        """
        st.session_state.current_page = page

    @staticmethod
    def get_selected_kb() -> Optional[str]:
        """
        获取选中的知识库 ID。

        Returns:
            知识库 ID，如果未选择则返回 None

        Example:
            >>> kb_id = SessionState.get_selected_kb()
            >>> if kb_id:
            ...     print(f"选中的知识库: {kb_id}")
        """
        return st.session_state.get("selected_kb_id", None)

    @staticmethod
    def set_selected_kb(kb_id: str):
        """
        设置选中的知识库。

        Args:
            kb_id: 知识库 ID

        Example:
            >>> SessionState.set_selected_kb("kb_123")
        """
        st.session_state.selected_kb_id = kb_id

    @staticmethod
    def get_kb_for_chat() -> Optional[str]:
        """
        获取聊天使用的知识库 ID。

        Returns:
            知识库 ID，如果未设置则返回 None

        Example:
            >>> kb_id = SessionState.get_kb_for_chat()
            >>> if kb_id:
            ...     print(f"聊天使用的知识库: {kb_id}")
        """
        return st.session_state.get("chat_kb_id", None)

    @staticmethod
    def set_kb_for_chat(kb_id: Optional[str]):
        """
        设置聊天使用的知识库。

        Args:
            kb_id: 知识库 ID，None 表示使用全部知识库

        Example:
            >>> SessionState.set_kb_for_chat("kb_123")
            >>> SessionState.set_kb_for_chat(None)  # 使用全部知识库
        """
        st.session_state.chat_kb_id = kb_id
