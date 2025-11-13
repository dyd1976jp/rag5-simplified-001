"""
Knowledge Base List Page

This module provides the knowledge base list page UI with card-based layout,
pagination, and CRUD operations.
"""

import logging
import time
from typing import Dict, Any
import streamlit as st

from .api_client import KnowledgeBaseAPIClient, APIError
from ...state import SessionState

logger = logging.getLogger(__name__)


def format_datetime(dt_str: str) -> str:
    """
    Format datetime string for display.
    
    Args:
        dt_str: ISO format datetime string
        
    Returns:
        Formatted datetime string (YYYY-MM-DD HH:MM)
        
    Example:
        >>> format_datetime("2024-01-15T10:30:00Z")
        '2024-01-15 10:30'
    """
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception as e:
        logger.warning(f"Failed to format datetime {dt_str}: {e}")
        return dt_str


def render_kb_list_page(api_client: KnowledgeBaseAPIClient):
    """
    Render the knowledge base list page.
    
    Displays knowledge bases in a 3x3 grid layout with pagination,
    create and delete operations.
    
    Args:
        api_client: API client instance
        
    Example:
        >>> api_client = KnowledgeBaseAPIClient()
        >>> render_kb_list_page(api_client)
    """
    st.title("📚 知识库管理")
    
    # Top action bar
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("管理您的知识库和文档")
    with col2:
        if st.button("➕ 新建知识库", use_container_width=True):
            render_create_kb_dialog(api_client)
    
    # Initialize page number in session state
    if "kb_list_page" not in st.session_state:
        st.session_state.kb_list_page = 1
    
    # Get knowledge base list
    try:
        with st.spinner("加载知识库列表..."):
            response = api_client.list_knowledge_bases(
                page=st.session_state.kb_list_page,
                size=9  # 3x3 grid
            )
            kbs = response.get("items", [])
            total = response.get("total", 0)
            total_pages = (total + 8) // 9  # Calculate total pages
            
            logger.info(f"Loaded {len(kbs)} knowledge bases (page {st.session_state.kb_list_page}/{total_pages})")
            
    except APIError as e:
        st.error(f"加载失败: {str(e)}")
        logger.error(f"Failed to load knowledge bases: {e}")
        return
    except Exception as e:
        st.error(f"加载失败: {str(e)}")
        logger.exception("Unexpected error loading knowledge bases")
        return
    
    # Display knowledge base cards
    if not kbs:
        st.info("暂无知识库，点击上方按钮创建第一个知识库")
        return
    
    # 3-column grid layout
    for i in range(0, len(kbs), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(kbs):
                kb = kbs[i + j]
                with col:
                    render_kb_card(kb, api_client)
    
    # Pagination controls
    if total_pages > 1:
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.session_state.kb_list_page > 1:
                if st.button("⬅️ 上一页", use_container_width=True):
                    st.session_state.kb_list_page -= 1
                    st.rerun()
        
        with col2:
            st.markdown(
                f"<div style='text-align: center; padding: 8px;'>第 {st.session_state.kb_list_page} / {total_pages} 页 (共 {total} 个知识库)</div>",
                unsafe_allow_html=True
            )
        
        with col3:
            if st.session_state.kb_list_page < total_pages:
                if st.button("下一页 ➡️", use_container_width=True):
                    st.session_state.kb_list_page += 1
                    st.rerun()


def render_kb_card(kb: Dict[str, Any], api_client: KnowledgeBaseAPIClient):
    """
    Render a single knowledge base card.
    
    Displays KB name, description, metadata, and action buttons.
    
    Args:
        kb: Knowledge base data dictionary
        api_client: API client instance
        
    Example:
        >>> kb = {"id": "kb_123", "name": "My KB", "description": "Test"}
        >>> render_kb_card(kb, api_client)
    """
    with st.container(border=True):
        # Title and description
        st.subheader(kb["name"])
        
        description = kb.get("description", "")
        if description:
            st.caption(description)
        else:
            st.caption("暂无描述")
        
        # Metadata
        st.text(f"ID: {kb['id'][:8]}...")
        
        # Format updated_at timestamp
        updated_at = kb.get("updated_at", "")
        if updated_at:
            st.text(f"更新: {format_datetime(updated_at)}")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("查看", key=f"view_{kb['id']}", use_container_width=True):
                SessionState.set_selected_kb(kb['id'])
                SessionState.set_current_page("kb_detail")
                st.rerun()
        
        with col2:
            if st.button("🗑️", key=f"delete_{kb['id']}", use_container_width=True, help="删除知识库"):
                show_delete_confirmation(kb, api_client)


@st.dialog("确认删除")
def show_delete_confirmation(kb: Dict[str, Any], api_client: KnowledgeBaseAPIClient):
    """
    Show delete confirmation dialog.
    
    Displays a warning dialog before deleting a knowledge base.
    
    Args:
        kb: Knowledge base data dictionary
        api_client: API client instance
        
    Example:
        >>> kb = {"id": "kb_123", "name": "My KB"}
        >>> show_delete_confirmation(kb, api_client)
    """
    st.warning(f"确定要删除知识库 **{kb['name']}** 吗？")
    st.error("此操作不可撤销，将删除所有相关文件和数据！")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("取消", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("确认删除", type="primary", use_container_width=True):
            try:
                with st.spinner("删除中..."):
                    api_client.delete_knowledge_base(kb['id'])
                    logger.info(f"Deleted knowledge base: {kb['id']}")
                
                st.success("删除成功")
                time.sleep(1)
                st.rerun()
                
            except APIError as e:
                st.error(f"删除失败: {str(e)}")
                logger.error(f"Failed to delete knowledge base {kb['id']}: {e}")
            except Exception as e:
                st.error(f"删除失败: {str(e)}")
                logger.exception(f"Unexpected error deleting knowledge base {kb['id']}")


@st.dialog("创建知识库")
def render_create_kb_dialog(api_client: KnowledgeBaseAPIClient):
    """
    Render create knowledge base dialog.
    
    Displays a form for creating a new knowledge base with configuration options.
    
    Args:
        api_client: API client instance
        
    Example:
        >>> api_client = KnowledgeBaseAPIClient()
        >>> render_create_kb_dialog(api_client)
    """
    st.subheader("新建知识库")
    
    # Basic information
    name = st.text_input("知识库名称*", placeholder="例如：产品文档")
    description = st.text_area("描述", placeholder="描述知识库内容（可选）")
    
    # Chunk configuration
    st.divider()
    st.markdown("**切片配置**")
    col1, col2 = st.columns(2)
    with col1:
        chunk_size = st.number_input("切片大小", min_value=100, max_value=2000, value=1000)
    with col2:
        chunk_overlap = st.number_input("切片重叠", min_value=0, max_value=200, value=50)
    
    # Embedding model
    st.divider()
    st.markdown("**向量模型**")
    embedding_model = st.selectbox(
        "选择向量模型",
        ["BAAI/bge-m3", "BAAI/bge-small-zh-v1.5"]
    )
    
    # Retrieval configuration
    st.divider()
    st.markdown("**检索配置**")
    col1, col2 = st.columns(2)
    with col1:
        top_k = st.slider("Top-K", min_value=1, max_value=20, value=5)
    with col2:
        similarity_threshold = st.slider(
            "相似度阈值", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.3,
            step=0.01
        )
    
    retrieval_mode = st.radio(
        "检索策略",
        ["vector", "fulltext", "hybrid"],
        format_func=lambda x: {"vector": "向量检索", "fulltext": "全文检索", "hybrid": "混合检索"}[x]
    )
    
    # Submit buttons
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("取消", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("创建", type="primary", use_container_width=True):
            if not name or not name.strip():
                st.error("请输入知识库名称")
                return
            
            try:
                kb_data = {
                    "name": name.strip(),
                    "description": description.strip() if description else "",
                    "embedding_model": embedding_model,
                    "chunk_config": {
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap
                    },
                    "retrieval_config": {
                        "retrieval_mode": retrieval_mode,
                        "top_k": top_k,
                        "similarity_threshold": similarity_threshold
                    }
                }
                
                with st.spinner("创建中..."):
                    result = api_client.create_knowledge_base(kb_data)
                    logger.info(f"Created knowledge base: {result['id']}")
                
                st.success("创建成功！")
                time.sleep(1)
                
                # Navigate to detail page
                SessionState.set_selected_kb(result['id'])
                SessionState.set_current_page("kb_detail")
                st.rerun()
                
            except APIError as e:
                st.error(f"创建失败: {str(e)}")
                logger.error(f"Failed to create knowledge base: {e}")
            except Exception as e:
                st.error(f"创建失败: {str(e)}")
                logger.exception("Unexpected error creating knowledge base")
