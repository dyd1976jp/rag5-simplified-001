"""
Knowledge Base Detail Page

This module provides the knowledge base detail page UI with tabs for
file management, settings, and retrieval testing.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import streamlit as st

from .api_client import KnowledgeBaseAPIClient, APIError
from ...state import SessionState

logger = logging.getLogger(__name__)


# ==================== Utility Functions ====================

def format_datetime(dt_str: str) -> str:
    """
    Format datetime string to readable format.
    
    Args:
        dt_str: ISO format datetime string
        
    Returns:
        Formatted datetime string (YYYY-MM-DD HH:MM)
        
    Example:
        >>> format_datetime("2024-01-15T10:30:00Z")
        '2024-01-15 10:30'
    """
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception as e:
        logger.warning(f"Failed to format datetime {dt_str}: {e}")
        return dt_str


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size string
        
    Example:
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
    """
    try:
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    except Exception as e:
        logger.warning(f"Failed to format file size {size_bytes}: {e}")
        return f"{size_bytes} B"


def render_kb_detail_page(api_client: KnowledgeBaseAPIClient):
    """
    Render the knowledge base detail page.
    
    Displays knowledge base information with three tabs:
    - File Management: Upload, view, and manage files
    - KB Settings: Configure knowledge base parameters
    - Retrieval Test: Test search functionality
    
    Args:
        api_client: API client instance
        
    Example:
        >>> api_client = KnowledgeBaseAPIClient()
        >>> render_kb_detail_page(api_client)
    """
    # Get selected knowledge base ID
    kb_id = SessionState.get_selected_kb()
    if not kb_id:
        st.error("未选择知识库")
        st.info("请从知识库列表中选择一个知识库")
        
        # Provide button to go back to list
        if st.button("返回知识库列表"):
            SessionState.set_current_page("kb_list")
            st.rerun()
        return
    
    # Fetch knowledge base details
    try:
        with st.spinner("加载知识库信息..."):
            kb = api_client.get_knowledge_base(kb_id)
            logger.info(f"Loaded knowledge base details: {kb_id}")
    except APIError as e:
        st.error(f"加载失败: {str(e)}")
        logger.error(f"Failed to load knowledge base {kb_id}: {e}")
        
        # Provide button to go back to list
        if st.button("返回知识库列表"):
            SessionState.set_current_page("kb_list")
            st.rerun()
        return
    except Exception as e:
        st.error(f"加载失败: {str(e)}")
        logger.exception(f"Unexpected error loading knowledge base {kb_id}")
        
        # Provide button to go back to list
        if st.button("返回知识库列表"):
            SessionState.set_current_page("kb_list")
            st.rerun()
        return
    
    # Top navigation and information
    render_kb_header(kb)
    
    # Tab navigation
    tab1, tab2, tab3 = st.tabs(["📁 文件管理", "⚙️ 知识库设置", "🔍 检索测试"])
    
    with tab1:
        render_file_management_tab(kb_id, api_client)
    
    with tab2:
        render_kb_settings_tab(kb, api_client)
    
    with tab3:
        render_retrieval_test_tab(kb_id, api_client)


def render_kb_header(kb: Dict[str, Any]):
    """
    Render knowledge base header with navigation and basic info.
    
    Args:
        kb: Knowledge base data dictionary
        
    Example:
        >>> kb = {"id": "kb_123", "name": "My KB", "description": "Test"}
        >>> render_kb_header(kb)
    """
    # Top navigation bar
    col1, col2 = st.columns([1, 5])
    
    with col1:
        if st.button("← 返回列表", use_container_width=True):
            SessionState.set_current_page("kb_list")
            st.rerun()
    
    with col2:
        st.title(kb["name"])
    
    # Knowledge base metadata
    st.caption(f"**ID:** {kb['id']}")
    
    description = kb.get("description", "")
    if description:
        st.caption(f"**描述:** {description}")
    else:
        st.caption("**描述:** 暂无描述")
    
    # Additional metadata in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        embedding_model = kb.get("embedding_model", "未设置")
        st.caption(f"**向量模型:** {embedding_model}")
    
    with col2:
        chunk_config = kb.get("chunk_config", {})
        chunk_size = chunk_config.get("chunk_size", "未设置")
        st.caption(f"**切片大小:** {chunk_size}")
    
    with col3:
        retrieval_config = kb.get("retrieval_config", {})
        retrieval_mode = retrieval_config.get("retrieval_mode", "未设置")
        mode_display = {
            "vector": "向量检索",
            "fulltext": "全文检索",
            "hybrid": "混合检索"
        }.get(retrieval_mode, retrieval_mode)
        st.caption(f"**检索策略:** {mode_display}")
    
    st.divider()


def render_file_management_tab(kb_id: str, api_client: KnowledgeBaseAPIClient):
    """
    Render file management tab with upload, list, search, and filter functionality.
    
    Provides complete file management interface including:
    - File upload (multiple files supported)
    - File list with pagination
    - Search and filter by status
    - File operations (delete, reprocess)
    - Status indicators with color coding
    
    Args:
        kb_id: Knowledge base ID
        api_client: API client instance
        
    Example:
        >>> render_file_management_tab("kb_123", api_client)
    """
    st.subheader("文件管理")
    
    # ==================== File Upload Section ====================
    st.markdown("### 📤 上传文件")
    
    uploaded_files = st.file_uploader(
        "选择文件（支持多文件上传）",
        accept_multiple_files=True,
        type=["txt", "md", "pdf", "docx", "doc"],
        key=f"file_uploader_{kb_id}",
        help="支持的文件格式：TXT, MD, PDF, DOCX"
    )
    
    if uploaded_files:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📎 已选择 {len(uploaded_files)} 个文件")
            # Show file names
            file_names = [f.name for f in uploaded_files]
            if len(file_names) <= 5:
                for name in file_names:
                    st.caption(f"  • {name}")
            else:
                for name in file_names[:3]:
                    st.caption(f"  • {name}")
                st.caption(f"  • ... 还有 {len(file_names) - 3} 个文件")
        
        with col2:
            upload_button_key = f"upload_btn_{kb_id}_{len(uploaded_files)}"
            if st.button("📤 开始上传", type="primary", use_container_width=True, key=upload_button_key):
                # Create progress container
                progress_container = st.empty()
                status_container = st.empty()
                
                try:
                    # Show initial progress
                    with progress_container:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                    
                    # Upload files one by one with progress updates
                    results = []
                    total_files = len(uploaded_files)
                    
                    for idx, file in enumerate(uploaded_files, 1):
                        # Update progress
                        progress = idx / total_files
                        progress_bar.progress(progress)
                        status_text.text(f"正在上传 {idx}/{total_files}: {file.name}")
                        
                        try:
                            # Upload single file
                            result = api_client.upload_files(kb_id, [file])
                            results.extend(result)
                            logger.info(f"Uploaded file {file.name} to KB {kb_id}")
                        except Exception as e:
                            logger.error(f"Failed to upload {file.name}: {e}")
                            # Continue with other files
                    
                    # Clear progress indicators
                    progress_container.empty()
                    
                    # Show final result
                    if len(results) == total_files:
                        status_container.success(f"✅ 成功上传 {len(results)} 个文件！文件将在后台处理。")
                    elif len(results) > 0:
                        status_container.warning(f"⚠️ 部分上传成功：{len(results)}/{total_files} 个文件")
                    else:
                        status_container.error(f"❌ 上传失败：所有文件上传失败")
                    
                    logger.info(f"Upload completed: {len(results)}/{total_files} files to KB {kb_id}")
                    
                    # Wait a moment for user to see the message
                    time.sleep(2)
                    
                    # Refresh the page to show updated file list
                    st.rerun()
                    
                except APIError as e:
                    progress_container.empty()
                    status_container.error(f"❌ 上传失败: {str(e)}")
                    logger.error(f"Failed to upload files to KB {kb_id}: {e}")
                except Exception as e:
                    progress_container.empty()
                    status_container.error(f"❌ 上传失败: {str(e)}")
                    logger.exception(f"Unexpected error uploading files to KB {kb_id}")
    
    st.divider()
    
    # ==================== File List Section ====================
    st.markdown("### 📋 文件列表")
    
    # Search and filter controls
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        search_query = st.text_input(
            "搜索文件名",
            key=f"file_search_{kb_id}",
            placeholder="输入文件名关键词...",
            label_visibility="collapsed"
        )
    
    with col2:
        status_options = {
            "all": "全部状态",
            "pending": "⏳ 等待中",
            "parsing": "🔄 解析中",
            "persisting": "💾 索引中",
            "succeeded": "✅ 成功",
            "failed": "❌ 失败"
        }
        
        status_filter = st.selectbox(
            "状态筛选",
            options=list(status_options.keys()),
            format_func=lambda x: status_options[x],
            key=f"status_filter_{kb_id}",
            label_visibility="collapsed"
        )
    
    with col3:
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()
    
    # Get current page from session state
    page_key = f"file_list_page_{kb_id}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    
    current_page = st.session_state[page_key]
    
    # Fetch file list
    try:
        with st.spinner("加载文件列表..."):
            response = api_client.list_files(
                kb_id,
                page=current_page,
                size=10,
                status=None if status_filter == "all" else status_filter,
                query=search_query if search_query else None
            )
            
            files = response.get("items", [])
            total = response.get("total", 0)
            total_pages = response.get("pages", 1)
            
            logger.info(f"Loaded {len(files)} files for KB {kb_id} (page {current_page}/{total_pages})")
    
    except APIError as e:
        st.error(f"❌ 加载文件列表失败: {str(e)}")
        logger.error(f"Failed to load files for KB {kb_id}: {e}")
        return
    except Exception as e:
        st.error(f"❌ 加载文件列表失败: {str(e)}")
        logger.exception(f"Unexpected error loading files for KB {kb_id}")
        return
    
    # Display file count and status summary
    if total > 0:
        st.caption(f"共 {total} 个文件")
    
    # Display files
    if not files:
        if search_query or status_filter != "all":
            st.info("🔍 未找到符合条件的文件")
        else:
            st.info("📭 暂无文件，请上传文件到知识库")
        return
    
    # Render each file
    for file in files:
        render_file_row(file, kb_id, api_client)
    
    # Pagination controls
    if total_pages > 1:
        st.divider()
        
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ 首页", disabled=(current_page == 1), use_container_width=True):
                st.session_state[page_key] = 1
                st.rerun()
        
        with col2:
            if st.button("◀️ 上一页", disabled=(current_page == 1), use_container_width=True):
                st.session_state[page_key] = current_page - 1
                st.rerun()
        
        with col3:
            st.markdown(f"<div style='text-align: center; padding: 8px;'>第 {current_page} / {total_pages} 页</div>", unsafe_allow_html=True)
        
        with col4:
            if st.button("下一页 ▶️", disabled=(current_page >= total_pages), use_container_width=True):
                st.session_state[page_key] = current_page + 1
                st.rerun()
        
        with col5:
            if st.button("末页 ⏭️", disabled=(current_page >= total_pages), use_container_width=True):
                st.session_state[page_key] = total_pages
                st.rerun()


def render_file_row(file: Dict[str, Any], kb_id: str, api_client: KnowledgeBaseAPIClient):
    """
    Render a single file row with status, metadata, and action buttons.
    
    Displays file information including:
    - File name and size
    - Processing status with color indicators
    - Creation timestamp
    - Action buttons (reprocess for failed files, delete)
    - Error details for failed files
    
    Args:
        file: File data dictionary
        kb_id: Knowledge base ID
        api_client: API client instance
        
    Example:
        >>> file = {
        ...     "id": "file_123",
        ...     "file_name": "doc.pdf",
        ...     "file_size": 1024000,
        ...     "status": "succeeded",
        ...     "created_at": "2024-01-15T10:30:00Z"
        ... }
        >>> render_file_row(file, "kb_123", api_client)
    """
    with st.container(border=True):
        # Main file information row
        col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1.5])
        
        # Column 1: File name and size
        with col1:
            st.markdown(f"**📄 {file['file_name']}**")
            file_size = file.get('file_size', 0)
            st.caption(f"大小: {format_file_size(file_size)}")
        
        # Column 2: Status with color indicator
        with col2:
            status = file.get('status', 'unknown')
            
            # Status display with emoji and color
            status_display = {
                "pending": ("⏳", "等待中", "🟡"),
                "parsing": ("🔄", "解析中", "🔵"),
                "persisting": ("💾", "索引中", "🔵"),
                "succeeded": ("✅", "成功", "🟢"),
                "failed": ("❌", "失败", "🔴"),
                "unknown": ("⚪", "未知", "⚪")
            }
            
            emoji, text, indicator = status_display.get(status, status_display["unknown"])
            st.markdown(f"{indicator} **{text}**")
        
        # Column 3: Timestamp
        with col3:
            created_at = file.get('created_at', '')
            if created_at:
                st.caption(f"🕒 {format_datetime(created_at)}")
            else:
                st.caption("🕒 未知时间")
        
        # Column 4: Action buttons
        with col4:
            btn_col1, btn_col2 = st.columns(2)
            
            # Reprocess button (only for failed files)
            with btn_col1:
                if status == 'failed':
                    reprocess_key = f"reprocess_{file['id']}"
                    if st.button(
                        "🔄",
                        key=reprocess_key,
                        help="重新处理",
                        use_container_width=True
                    ):
                        # Show progress indicator
                        with st.spinner("正在提交重新处理请求..."):
                            try:
                                # Try to call reprocess API
                                result = api_client.reprocess_file(kb_id, file['id'])
                                st.success("✅ 文件已加入重新处理队列")
                                logger.info(f"Reprocess requested for file {file['id']} in KB {kb_id}")
                                time.sleep(1)
                                st.rerun()
                            except APIError as e:
                                # Check if it's a "not implemented" error
                                if hasattr(e, 'status_code') and e.status_code == 501:
                                    st.warning("⚠️ 重新处理功能暂未在后端实现。请删除文件后重新上传。")
                                    logger.warning(f"Reprocess endpoint not implemented for file {file['id']}")
                                else:
                                    st.error(f"❌ 操作失败: {str(e)}")
                                    logger.error(f"Failed to reprocess file {file['id']}: {e}")
                            except Exception as e:
                                st.error(f"❌ 操作失败: {str(e)}")
                                logger.exception(f"Unexpected error reprocessing file {file['id']}")
            
            # Delete button
            with btn_col2:
                delete_key = f"del_file_{file['id']}"
                if st.button(
                    "🗑️",
                    key=delete_key,
                    help="删除文件",
                    use_container_width=True
                ):
                    # Show confirmation dialog
                    show_delete_file_confirmation(file, kb_id, api_client)
        
        # Show error details for failed files
        if status == 'failed':
            failed_reason = file.get('failed_reason', '')
            if failed_reason:
                with st.expander("🔍 查看错误详情", expanded=False):
                    st.error(failed_reason)
            else:
                with st.expander("🔍 查看错误详情", expanded=False):
                    st.warning("未提供错误详情")


@st.dialog("确认删除文件")
def show_delete_file_confirmation(file: Dict[str, Any], kb_id: str, api_client: KnowledgeBaseAPIClient):
    """
    Show file deletion confirmation dialog.
    
    Displays a confirmation dialog before deleting a file from the knowledge base.
    Provides clear warning about the irreversible nature of the operation.
    
    Args:
        file: File data dictionary
        kb_id: Knowledge base ID
        api_client: API client instance
        
    Example:
        >>> file = {"id": "file_123", "file_name": "doc.pdf"}
        >>> show_delete_file_confirmation(file, "kb_123", api_client)
    """
    st.warning(f"⚠️ 确定要删除文件 **{file['file_name']}** 吗？")
    st.error("🚨 此操作不可撤销！文件及其所有相关数据将被永久删除。")
    
    # Show file details
    with st.expander("📄 文件详情"):
        st.text(f"文件名: {file['file_name']}")
        st.text(f"文件ID: {file['id']}")
        st.text(f"大小: {format_file_size(file.get('file_size', 0))}")
        st.text(f"状态: {file.get('status', 'unknown')}")
        if file.get('chunk_count', 0) > 0:
            st.text(f"文档块数: {file['chunk_count']}")
    
    st.divider()
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("❌ 取消", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("🗑️ 确认删除", type="primary", use_container_width=True):
            # Show progress
            with st.spinner("正在删除文件..."):
                try:
                    # Delete the file
                    api_client.delete_file(kb_id, file['id'])
                    
                    # Show success message
                    st.success("✅ 文件删除成功！")
                    logger.info(f"Deleted file {file['id']} from KB {kb_id}")
                    
                    # Wait for user to see the message
                    time.sleep(1)
                    
                    # Refresh the page
                    st.rerun()
                    
                except APIError as e:
                    st.error(f"❌ 删除失败: {str(e)}")
                    logger.error(f"Failed to delete file {file['id']}: {e}")
                except Exception as e:
                    st.error(f"❌ 删除失败: {str(e)}")
                    logger.exception(f"Unexpected error deleting file {file['id']}")


def render_kb_settings_tab(kb: Dict[str, Any], api_client: KnowledgeBaseAPIClient):
    """
    Render knowledge base settings tab with editable configuration form.
    
    Provides a comprehensive settings interface for:
    - Basic information (name, description)
    - Chunk configuration (chunk_size, chunk_overlap)
    - Retrieval configuration (top_k, similarity_threshold, retrieval_mode)
    
    Uses st.form to batch updates and prevent unnecessary reruns.
    Validates input and provides clear feedback on save success/failure.
    
    Args:
        kb: Knowledge base data dictionary
        api_client: API client instance
        
    Example:
        >>> kb = {
        ...     "id": "kb_123",
        ...     "name": "My KB",
        ...     "description": "Test KB",
        ...     "chunk_config": {"chunk_size": 512, "chunk_overlap": 50},
        ...     "retrieval_config": {"top_k": 5, "similarity_threshold": 0.3, "retrieval_mode": "vector"}
        ... }
        >>> render_kb_settings_tab(kb, api_client)
    """
    st.subheader("⚙️ 知识库设置")
    st.markdown("修改知识库的配置参数。更改将立即生效。")
    
    st.divider()
    
    # Create form for settings
    with st.form("kb_settings_form", clear_on_submit=False):
        # ==================== Basic Information ====================
        st.markdown("### 📋 基本信息")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            name = st.text_input(
                "知识库名称 *",
                value=kb.get("name", ""),
                max_chars=100,
                help="知识库的显示名称（必填）",
                placeholder="例如：产品文档知识库"
            )
        
        with col2:
            embedding_model = st.text_input(
                "向量模型",
                value=kb.get("embedding_model", ""),
                disabled=True,
                help="向量模型创建后不可修改"
            )
        
        description = st.text_area(
            "描述",
            value=kb.get("description", ""),
            max_chars=500,
            height=100,
            help="知识库的详细描述（可选）",
            placeholder="描述知识库的用途和内容..."
        )
        
        st.divider()
        
        # ==================== Chunk Configuration ====================
        st.markdown("### 📄 切片配置")
        st.caption("控制文档如何被分割成小块进行向量化")
        
        col1, col2 = st.columns(2)
        
        # Get current chunk config
        chunk_config = kb.get("chunk_config", {})
        current_chunk_size = chunk_config.get("chunk_size", 512)
        current_chunk_overlap = chunk_config.get("chunk_overlap", 50)
        
        with col1:
            chunk_size = st.number_input(
                "切片大小",
                min_value=100,
                max_value=2000,
                value=current_chunk_size,
                step=50,
                help="每个文档块的字符数。较大的值保留更多上下文，较小的值提供更精确的检索。"
            )
        
        with col2:
            chunk_overlap = st.number_input(
                "切片重叠",
                min_value=0,
                max_value=500,
                value=current_chunk_overlap,
                step=10,
                help="相邻文档块之间重叠的字符数。重叠有助于保持上下文连续性。"
            )
        
        # Show chunk configuration preview
        with st.expander("💡 切片配置说明"):
            st.markdown("""
            **切片大小 (Chunk Size):**
            - 推荐值：512-1024 字符
            - 较大值（1000+）：适合需要更多上下文的场景
            - 较小值（300-500）：适合精确检索和问答
            
            **切片重叠 (Chunk Overlap):**
            - 推荐值：10-20% 的切片大小
            - 重叠可以防止重要信息在切片边界处丢失
            - 过大的重叠会增加存储和检索成本
            """)
        
        st.divider()
        
        # ==================== Retrieval Configuration ====================
        st.markdown("### 🔍 检索配置")
        st.caption("控制如何从知识库中检索相关内容")
        
        # Get current retrieval config
        retrieval_config = kb.get("retrieval_config", {})
        current_top_k = retrieval_config.get("top_k", 5)
        current_similarity_threshold = retrieval_config.get("similarity_threshold", 0.3)
        current_retrieval_mode = retrieval_config.get("retrieval_mode", "vector")
        
        col1, col2 = st.columns(2)
        
        with col1:
            top_k = st.slider(
                "Top-K",
                min_value=1,
                max_value=20,
                value=current_top_k,
                step=1,
                help="返回最相关的 K 个文档块。较大的值提供更多上下文，但可能包含不太相关的内容。"
            )
        
        with col2:
            similarity_threshold = st.slider(
                "相似度阈值",
                min_value=0.0,
                max_value=1.0,
                value=float(current_similarity_threshold),
                step=0.01,
                format="%.2f",
                help="只返回相似度高于此阈值的结果。较高的值返回更相关但可能更少的结果。"
            )
        
        # Retrieval mode selection
        retrieval_mode_options = {
            "vector": "向量检索",
            "fulltext": "全文检索",
            "hybrid": "混合检索"
        }
        
        # Find current index
        mode_keys = list(retrieval_mode_options.keys())
        current_mode_index = mode_keys.index(current_retrieval_mode) if current_retrieval_mode in mode_keys else 0
        
        retrieval_mode = st.radio(
            "检索策略",
            options=mode_keys,
            index=current_mode_index,
            format_func=lambda x: retrieval_mode_options[x],
            help="选择检索方法",
            horizontal=True
        )
        
        # Show retrieval configuration explanation
        with st.expander("💡 检索策略说明"):
            st.markdown("""
            **向量检索 (Vector):**
            - 基于语义相似度的检索
            - 适合理解查询意图和同义词
            - 推荐用于大多数场景
            
            **全文检索 (Fulltext):**
            - 基于关键词匹配的检索
            - 适合精确的术语和专有名词查找
            - 对拼写敏感
            
            **混合检索 (Hybrid):**
            - 结合向量和全文检索的优势
            - 提供最全面的检索结果
            - 计算成本较高
            """)
        
        st.divider()
        
        # ==================== Form Submission ====================
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col2:
            cancel_button = st.form_submit_button(
                "🔄 重置",
                use_container_width=True,
                help="重置为当前保存的值"
            )
        
        with col3:
            submit_button = st.form_submit_button(
                "💾 保存设置",
                type="primary",
                use_container_width=True,
                help="保存所有更改"
            )
        
        # Handle form submission
        if cancel_button:
            st.info("ℹ️ 表单已重置，请刷新页面查看原始值")
            st.rerun()
        
        if submit_button:
            # Validate input
            validation_errors = []
            
            if not name or not name.strip():
                validation_errors.append("❌ 知识库名称不能为空")
            
            if len(name) > 100:
                validation_errors.append("❌ 知识库名称不能超过 100 个字符")
            
            if chunk_size < 100 or chunk_size > 2000:
                validation_errors.append("❌ 切片大小必须在 100-2000 之间")
            
            if chunk_overlap < 0 or chunk_overlap >= chunk_size:
                validation_errors.append("❌ 切片重叠必须在 0 到切片大小之间")
            
            if top_k < 1 or top_k > 20:
                validation_errors.append("❌ Top-K 必须在 1-20 之间")
            
            if similarity_threshold < 0.0 or similarity_threshold > 1.0:
                validation_errors.append("❌ 相似度阈值必须在 0.0-1.0 之间")
            
            # Show validation errors
            if validation_errors:
                for error in validation_errors:
                    st.error(error)
                st.stop()
            
            # Prepare update data
            update_data = {
                "name": name.strip(),
                "description": description.strip() if description else "",
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
            
            # Show progress indicator
            with st.spinner("正在保存设置..."):
                try:
                    # Call update API
                    updated_kb = api_client.update_knowledge_base(kb["id"], update_data)
                    
                    # Show success message
                    st.success("✅ 设置保存成功！")
                    logger.info(f"Updated knowledge base {kb['id']} settings")
                    
                    # Wait for user to see the message
                    time.sleep(1.5)
                    
                    # Refresh the page to show updated values
                    st.rerun()
                    
                except APIError as e:
                    st.error(f"❌ 保存失败: {str(e)}")
                    logger.error(f"Failed to update knowledge base {kb['id']}: {e}")
                    
                except Exception as e:
                    st.error(f"❌ 保存失败: {str(e)}")
                    logger.exception(f"Unexpected error updating knowledge base {kb['id']}")
    
    # Show current configuration summary below the form
    st.divider()
    st.markdown("### 📊 当前配置摘要")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="切片大小",
            value=f"{chunk_config.get('chunk_size', 'N/A')} 字符"
        )
        st.metric(
            label="切片重叠",
            value=f"{chunk_config.get('chunk_overlap', 'N/A')} 字符"
        )
    
    with col2:
        st.metric(
            label="Top-K",
            value=retrieval_config.get('top_k', 'N/A')
        )
        st.metric(
            label="相似度阈值",
            value=f"{retrieval_config.get('similarity_threshold', 'N/A'):.2f}"
        )
    
    with col3:
        mode_display = retrieval_mode_options.get(
            retrieval_config.get('retrieval_mode', 'vector'),
            'N/A'
        )
        st.metric(
            label="检索策略",
            value=mode_display
        )
        st.metric(
            label="向量模型",
            value=kb.get('embedding_model', 'N/A')[:20] + "..." if len(kb.get('embedding_model', '')) > 20 else kb.get('embedding_model', 'N/A')
        )


def render_retrieval_test_tab(kb_id: str, api_client: KnowledgeBaseAPIClient):
    """
    Render retrieval test tab for testing knowledge base search functionality.
    
    Provides an interactive interface to test retrieval with:
    - Query input field
    - Adjustable Top-K parameter
    - Search results with similarity scores
    - Document content and metadata display
    - Empty state handling
    
    Args:
        kb_id: Knowledge base ID
        api_client: API client instance
        
    Example:
        >>> render_retrieval_test_tab("kb_123", api_client)
    """
    st.subheader("🔍 检索测试")
    st.markdown("测试知识库的检索效果，查看相关文档和相似度分数。")
    
    st.divider()
    
    # ==================== Query Input Section ====================
    st.markdown("### 🔎 输入查询")
    
    # Query input
    query = st.text_input(
        "查询内容",
        placeholder="例如：什么是 RAG？",
        help="输入您想要搜索的问题或关键词",
        key=f"retrieval_test_query_{kb_id}",
        label_visibility="collapsed"
    )
    
    # Top-K slider and search button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        top_k = st.slider(
            "返回结果数量 (Top-K)",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            help="返回最相关的 K 个文档块。较大的值提供更多上下文。",
            key=f"retrieval_test_topk_{kb_id}"
        )
    
    with col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)  # Spacing
        search_button = st.button(
            "🔍 搜索",
            type="primary",
            use_container_width=True,
            disabled=not query or not query.strip(),
            key=f"retrieval_test_search_{kb_id}"
        )
    
    # Optional: Advanced settings in expander
    with st.expander("⚙️ 高级设置"):
        use_custom_threshold = st.checkbox(
            "使用自定义相似度阈值",
            value=False,
            help="覆盖知识库默认的相似度阈值",
            key=f"use_custom_threshold_{kb_id}"
        )
        
        if use_custom_threshold:
            custom_threshold = st.slider(
                "相似度阈值",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.01,
                format="%.2f",
                help="只返回相似度高于此阈值的结果",
                key=f"custom_threshold_{kb_id}"
            )
        else:
            custom_threshold = None
    
    st.divider()
    
    # ==================== Search Results Section ====================
    
    # Only perform search when button is clicked
    if search_button and query and query.strip():
        st.markdown("### 📊 检索结果")
        
        # Show search parameters
        with st.expander("🔧 搜索参数", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("查询内容", f'"{query[:30]}..."' if len(query) > 30 else f'"{query}"')
            with col2:
                st.metric("Top-K", top_k)
            with col3:
                if custom_threshold is not None:
                    st.metric("相似度阈值", f"{custom_threshold:.2f}")
                else:
                    st.metric("相似度阈值", "使用默认值")
        
        # Perform search
        with st.spinner("🔍 正在搜索..."):
            try:
                # Call query API
                results = api_client.query_knowledge_base(
                    kb_id=kb_id,
                    query=query.strip(),
                    top_k=top_k,
                    similarity_threshold=custom_threshold
                )
                
                logger.info(f"Retrieved {len(results)} results for query in KB {kb_id}")
                
            except APIError as e:
                st.error(f"❌ 搜索失败: {str(e)}")
                logger.error(f"Failed to query KB {kb_id}: {e}")
                return
            except Exception as e:
                st.error(f"❌ 搜索失败: {str(e)}")
                logger.exception(f"Unexpected error querying KB {kb_id}")
                return
        
        # Display results
        if not results or len(results) == 0:
            st.info("🔍 未找到相关内容")
            st.markdown("""
            **建议：**
            - 尝试使用不同的关键词
            - 降低相似度阈值
            - 增加 Top-K 值
            - 确保知识库中已上传并成功处理相关文档
            """)
            return
        
        # Show result count
        st.success(f"✅ 找到 {len(results)} 条相关结果")
        
        # Display each result in an expander
        for i, result in enumerate(results, 1):
            # Extract result data
            score = result.get('score', 0.0)
            text = result.get('text', result.get('content', ''))
            metadata = result.get('metadata', {})
            
            # Create expander title with score
            score_percentage = score * 100
            
            # Color code based on score
            if score >= 0.7:
                score_color = "🟢"  # Green for high relevance
            elif score >= 0.5:
                score_color = "🟡"  # Yellow for medium relevance
            else:
                score_color = "🟠"  # Orange for lower relevance
            
            expander_title = f"{score_color} 结果 {i} - 相似度: {score:.4f} ({score_percentage:.2f}%)"
            
            with st.expander(expander_title, expanded=(i == 1)):  # Expand first result by default
                # Display content
                st.markdown("**📄 内容:**")
                
                # Show text in a nice container
                st.text_area(
                    "文档内容",
                    value=text,
                    height=150,
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"result_text_{kb_id}_{i}"
                )
                
                st.divider()
                
                # Display metadata
                st.markdown("**📋 元数据:**")
                
                if metadata:
                    # Display metadata in columns for better layout
                    metadata_cols = st.columns(2)
                    
                    # Common metadata fields
                    common_fields = ['file_name', 'file_id', 'chunk_id', 'page', 'source']
                    other_fields = [k for k in metadata.keys() if k not in common_fields]
                    
                    col_idx = 0
                    
                    # Display common fields first
                    for field in common_fields:
                        if field in metadata:
                            with metadata_cols[col_idx % 2]:
                                value = metadata[field]
                                # Format field name
                                field_display = field.replace('_', ' ').title()
                                st.caption(f"**{field_display}:** {value}")
                            col_idx += 1
                    
                    # Display other fields
                    for field in other_fields:
                        with metadata_cols[col_idx % 2]:
                            value = metadata[field]
                            field_display = field.replace('_', ' ').title()
                            st.caption(f"**{field_display}:** {value}")
                        col_idx += 1
                    
                    # Show full metadata as JSON in a collapsible section
                    with st.expander("🔍 查看完整元数据 (JSON)", expanded=False):
                        st.json(metadata)
                else:
                    st.caption("_无元数据_")
                
                st.divider()
                
                # Display score details
                st.markdown("**📊 相似度详情:**")
                
                # Score visualization
                score_col1, score_col2, score_col3 = st.columns(3)
                
                with score_col1:
                    st.metric("相似度分数", f"{score:.4f}")
                
                with score_col2:
                    st.metric("百分比", f"{score_percentage:.2f}%")
                
                with score_col3:
                    # Relevance level
                    if score >= 0.7:
                        relevance = "高度相关"
                        relevance_color = "🟢"
                    elif score >= 0.5:
                        relevance = "中度相关"
                        relevance_color = "🟡"
                    elif score >= 0.3:
                        relevance = "低度相关"
                        relevance_color = "🟠"
                    else:
                        relevance = "弱相关"
                        relevance_color = "🔴"
                    
                    st.metric("相关性", f"{relevance_color} {relevance}")
                
                # Progress bar for visual score representation
                st.progress(min(score, 1.0))
        
        st.divider()
        
        # Summary statistics
        st.markdown("### 📈 检索统计")
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("结果数量", len(results))
        
        with stat_col2:
            avg_score = sum(r.get('score', 0) for r in results) / len(results) if results else 0
            st.metric("平均相似度", f"{avg_score:.4f}")
        
        with stat_col3:
            max_score = max((r.get('score', 0) for r in results), default=0)
            st.metric("最高相似度", f"{max_score:.4f}")
        
        with stat_col4:
            min_score = min((r.get('score', 0) for r in results), default=0)
            st.metric("最低相似度", f"{min_score:.4f}")
    
    elif not query or not query.strip():
        # Show helpful message when no query
        st.info("💡 请在上方输入查询内容，然后点击搜索按钮开始检索测试。")
        
        # Show example queries
        st.markdown("### 💭 示例查询")
        st.markdown("""
        您可以尝试以下类型的查询：
        - **问题式查询**: "什么是机器学习？"
        - **关键词查询**: "深度学习 神经网络"
        - **具体概念**: "RAG 检索增强生成"
        - **技术术语**: "向量数据库 embedding"
        """)
