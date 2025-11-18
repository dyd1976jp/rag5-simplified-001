"""
聊天页面模块。

本模块实现聊天界面的渲染和交互逻辑。
"""

import streamlit as st
import logging
from typing import Optional, Dict, Any

from rag5.core.agent.agent import ask
from rag5.config.settings import settings
from rag5.interfaces.ui.state import SessionState
from rag5.interfaces.ui.components import (
    render_page_header,
    render_chat_history,
    render_error,
    render_sidebar
)
from rag5.interfaces.ui.pages.knowledge_base.api_client import APIError, KnowledgeBaseAPIClient

logger = logging.getLogger(__name__)


def handle_user_input(prompt: str, kb_id: Optional[str] = None):
    """
    处理用户输入。

    Args:
        prompt: 用户输入的查询
        kb_id: 可选的知识库 ID，用于指定搜索的知识库

    Returns:
        生成的响应文本
    """
    # 输入验证
    normalized_prompt = prompt.strip()

    if not normalized_prompt:
        SessionState.set_error("请输入有效的问题。")
        SessionState.set_last_retrieval_context({})
        return None

    if len(normalized_prompt) > settings.max_query_length:
        SessionState.set_error(f"问题长度不能超过 {settings.max_query_length} 个字符。")
        SessionState.set_last_retrieval_context({})
        return None

    # 添加用户消息
    SessionState.add_message("user", prompt)

    # 准备历史记录（排除当前消息，限制为最近 20 条）
    history = SessionState.get_history(limit=20)

    # 调用代理（传入知识库 ID）
    try:
        response = ask(normalized_prompt, history, kb_id=kb_id)
    except ConnectionError as e:
        error_msg = f"连接错误：{str(e)}。请确保 Ollama 和 Qdrant 服务正在运行。"
        logger.error(error_msg)
        SessionState.set_last_retrieval_context({})
        return error_msg
    except ValueError as e:
        error_msg = f"配置错误：{str(e)}"
        logger.error(error_msg)
        SessionState.set_last_retrieval_context({})
        return error_msg
    except Exception as e:
        error_msg = f"抱歉，处理您的问题时出现错误：{str(e)}"
        logger.error(error_msg, exc_info=True)
        SessionState.set_last_retrieval_context({})
        return error_msg
    else:
        _fetch_retrieval_context(normalized_prompt, kb_id)
        return response


def _fetch_retrieval_context(query: str, kb_id: Optional[str]) -> None:
    """
    Fetch knowledge-base retrieval results and persist context.
    """
    if not query or not kb_id:
        SessionState.set_last_retrieval_context({})
        return

    context: Dict[str, Any] = {
        "query": query,
        "kb_id": kb_id,
        "results": [],
        "error": None
    }

    try:
        with KnowledgeBaseAPIClient() as api_client:
            results = api_client.query_knowledge_base(
                kb_id=kb_id,
                query=query,
                top_k=settings.top_k,
                similarity_threshold=settings.similarity_threshold
            )
        context["results"] = results
    except APIError as e:
        logger.warning(f"知识库查询失败: {e}")
        context["error"] = str(e)
    except Exception as e:
        logger.warning(f"知识库查询异常: {e}", exc_info=True)
        context["error"] = str(e)

    SessionState.set_last_retrieval_context(context)


def render_chat_interface():
    """
    渲染聊天界面。

    包括消息历史显示和用户输入处理。
    """
    # 显示错误消息（如果有）
    error = SessionState.get_error()
    if error:
        render_error(error)
        SessionState.clear_error()

    # 显示对话历史
    messages = SessionState.get_messages()
    render_chat_history(messages)

    # 获取选定的知识库 ID
    kb_id = SessionState.get_kb_for_chat()

    # 处理用户输入
    if prompt := st.chat_input("请输入您的问题...", max_chars=settings.max_query_length):
        clean_query = prompt.strip()

        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt)

        # 显示助手响应
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response = handle_user_input(prompt, kb_id=kb_id)

                if response:
                    # 检查是否是错误响应
                    if (response.startswith("抱歉") or
                        response.startswith("连接错误") or
                        response.startswith("配置错误")):
                        st.warning(response)
                    else:
                        st.markdown(response)

                    # 添加助手响应到历史
                    SessionState.add_message("assistant", response)
                else:
                    # 如果没有响应，触发重新运行以显示错误
                    st.rerun()

        # 显示检索结果（如果存在）
        retrieval_context = SessionState.get_last_retrieval_context()
        if (
            clean_query
            and retrieval_context
            and retrieval_context.get("query") == clean_query
            and retrieval_context.get("kb_id")
        ):
            kb_label = retrieval_context.get("kb_id")
            with st.expander(f"🔎 检索结果（KB: {kb_label}）", expanded=True):
                error_message = retrieval_context.get("error")
                if error_message:
                    st.warning(f"知识库查询失败：{error_message}")
                else:
                    results = retrieval_context.get("results", [])
                    if results:
                        for idx, result in enumerate(results, 1):
                            source = result.get("source") or result.get("metadata", {}).get("source", "文档")
                            score = result.get("score", 0.0)
                            st.markdown(f"**{idx}. {source}** · 相似度: {score:.4f}")
                            snippet = result.get("text", "").strip().replace("\n", " ")
                            if snippet:
                                if len(snippet) > 400:
                                    snippet = snippet[:400] + "…"
                                st.markdown(f"> {snippet}")
                            file_id = result.get("file_id", "-")
                            chunk_index = result.get("chunk_index", "-")
                            st.caption(f"文件: {file_id} · 块索引: {chunk_index}")
                            metadata = result.get("metadata", {})
                            if metadata:
                                meta_items = ", ".join(f"{k}: {v}" for k, v in metadata.items())
                                st.caption(f"元数据: {meta_items}")
                            if idx < len(results):
                                st.divider()
                    else:
                        st.info("未命中任何文档，建议调整关键词或更换知识库。")


def render_chat_page():
    """
    渲染聊天页面。

    包括页面标题、聊天界面和侧边栏。
    """
    # 渲染页面标题
    render_page_header()

    # 渲染侧边栏（包括知识库选择器）
    render_kb_selector_sidebar()

    # 渲染聊天界面
    render_chat_interface()

    # 渲染原有侧边栏功能
    messages = SessionState.get_messages()
    turn_count = SessionState.get_turn_count()

    if render_sidebar(turn_count, len(messages)):
        # 清空对话
        SessionState.clear_messages()
        SessionState.clear_error()
        st.rerun()


def render_kb_selector_sidebar():
    """
    在侧边栏渲染知识库选择器。
    
    允许用户选择特定知识库或使用全部知识库进行查询。
    """
    with st.sidebar:
        st.divider()
        st.subheader("🎯 知识库选择")
        
        try:
            # 导入 API 客户端
            from rag5.interfaces.ui.pages.knowledge_base.api_client import KnowledgeBaseAPIClient
            
            # 创建 API 客户端
            api_client = KnowledgeBaseAPIClient()
            
            # 获取知识库列表
            response = api_client.list_knowledge_bases(page=1, size=100)
            kbs = response.get("items", [])
            
            # 准备选项
            kb_options = ["默认（全部知识库）"] + [kb["name"] for kb in kbs]
            kb_ids = [None] + [kb["id"] for kb in kbs]
            
            # 获取当前选择的索引
            current_kb_id = SessionState.get_kb_for_chat()
            try:
                current_index = kb_ids.index(current_kb_id) if current_kb_id in kb_ids else 0
            except ValueError:
                current_index = 0
            
            # 渲染选择器
            selected_index = st.selectbox(
                "选择知识库",
                range(len(kb_options)),
                format_func=lambda i: kb_options[i],
                index=current_index,
                key="chat_kb_selector"
            )
            
            # 更新会话状态
            selected_kb_id = kb_ids[selected_index]
            SessionState.set_kb_for_chat(selected_kb_id)
            
            # 显示当前使用的知识库
            if selected_kb_id:
                st.info(f"✓ 当前使用: {kb_options[selected_index]}")
                st.caption(f"ID: {selected_kb_id[:8]}...")
            else:
                st.info("✓ 当前使用: 全部知识库")
                st.caption("将搜索默认知识库中的所有文档")
        
        except Exception as e:
            st.warning(f"⚠️ 无法加载知识库列表")
            st.caption(f"错误: {str(e)}")
            st.caption("将使用默认知识库")
            # 确保设置为 None（使用默认）
            SessionState.set_kb_for_chat(None)
