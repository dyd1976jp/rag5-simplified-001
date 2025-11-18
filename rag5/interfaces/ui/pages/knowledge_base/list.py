"""
Knowledge Base List Page

This module provides the knowledge base list page UI with card-based layout,
pagination, and CRUD operations.
"""

import logging
import time
from typing import Dict, Any, List, Optional
import streamlit as st

from .api_client import KnowledgeBaseAPIClient, APIError
from ...state import SessionState

# 导入配置
try:
    from rag5.config import settings
except ImportError:
    settings = None

from rag5.utils.embedding_models import (
    build_fallback_model_infos,
    normalize_model_name,
    resolve_embedding_dimension,
)

logger = logging.getLogger(__name__)
DEFAULT_VECTOR_DIMENSION = getattr(settings, "vector_dim", 1024) if settings else 1024


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
    kb_name = st.text_input(
        "知识库名称*",
        placeholder="例如：product_docs 或 my-kb",
        help="只能包含字母、数字、下划线和连字符，长度 2-64 个字符"
    )
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
    col_title, col_refresh = st.columns([3, 1])
    with col_title:
        st.markdown("**向量模型**")
    with col_refresh:
        if st.button("🔄 刷新", key="refresh_models_top", use_container_width=True, help="刷新模型列表"):
            st.rerun()

    # 添加"显示所有模型"选项
    show_all_models = st.checkbox(
        "显示所有 Ollama 模型（包括通用模型）",
        value=False,
        help="勾选后会显示 Ollama 中的所有模型，包括非嵌入模型。不推荐使用通用模型作为嵌入模型。"
    )

    default_model = settings.embed_model if settings else "bge-m3"
    model_entries: List[Dict[str, Any]] = []
    model_dimensions: Dict[str, int] = {}
    model_labels: Dict[str, str] = {}
    model_warning: Optional[str] = None
    source = "unknown"

    try:
        with st.spinner("加载可用向量模型..."):
            models_response = api_client.list_embedding_models(include_all=show_all_models)
        default_model = models_response.get("default_model") or default_model
        source = models_response.get("source") or "unknown"
        for model in models_response.get("models", []):
            model_name = model.get("name")
            if not model_name:
                continue
            dimension = model.get("dimension")
            label = model.get("display_name") or model_name
            if isinstance(dimension, (int, float)):
                model_dimensions[model_name] = int(dimension)
                label = f"{label} ({int(dimension)}d)"
            model_entries.append({
                "name": model_name,
                "label": label,
                "dimension": model_dimensions.get(model_name)
            })
            model_labels[model_name] = label
        if models_response.get("error"):
            model_warning = models_response["error"]
    except APIError as e:
        model_warning = str(e)
    except Exception as e:
        model_warning = str(e)
        logger.exception("加载嵌入模型列表失败")

    if not model_entries:
        model_warning = model_warning or "Ollama 未返回可用的嵌入模型，将使用预设列表。"
        fallback_infos = build_fallback_model_infos(DEFAULT_VECTOR_DIMENSION, [default_model])
        for info in fallback_infos:
            model_name = info["name"]
            dimension = info.get("dimension")
            label = info.get("display_name") or model_name
            if isinstance(dimension, (int, float)):
                model_dimensions[model_name] = int(dimension)
                label = f"{label} ({int(dimension)}d)"
            model_entries.append({
                "name": model_name,
                "label": label,
                "dimension": model_dimensions.get(model_name)
            })
            model_labels[model_name] = label

    if model_warning:
        st.warning(f"{model_warning}")
    elif source == "ollama":
        st.caption(f"已从 Ollama 加载 {len(model_entries)} 个嵌入模型")

    available_models = [entry["name"] for entry in model_entries]

    def _resolve_dimension(name: str) -> int:
        stored = model_dimensions.get(name)
        if stored:
            return stored
        return resolve_embedding_dimension(name, DEFAULT_VECTOR_DIMENSION)

    # 确定默认选择的索引（智能匹配带标签和不带标签的版本）
    default_index = 0
    if default_model:
        try:
            if default_model in available_models:
                default_index = available_models.index(default_model)
            elif f"{default_model}:latest" in available_models:
                default_index = available_models.index(f"{default_model}:latest")
            elif ":" in default_model:
                base_model = default_model.split(":")[0]
                if base_model in available_models:
                    default_index = available_models.index(base_model)
        except (ValueError, AttributeError):
            default_index = 0

    embedding_model = st.selectbox(
        "选择向量模型",
        options=available_models,
        index=default_index,
        help=f"从服务获取可用模型。默认: {default_model}",
        format_func=lambda value: model_labels.get(value, value)
    )

    embedding_dimension = _resolve_dimension(embedding_model)
    normalized_name = normalize_model_name(embedding_model)
    if embedding_model in model_dimensions:
        st.caption(f"✅ 该模型向量维度: {embedding_dimension}")
    else:
        st.caption(
            f"ℹ️ 未识别模型维度（{normalized_name}），使用默认 {embedding_dimension} "
            "（可在 .env 中通过 VECTOR_DIM 配置）"
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
            if not kb_name or not kb_name.strip():
                st.error("请输入知识库名称")
                return

            # 验证名称格式
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', kb_name.strip()):
                st.error("知识库名称只能包含字母、数字、下划线和连字符")
                return

            if len(kb_name.strip()) < 2 or len(kb_name.strip()) > 64:
                st.error("知识库名称长度必须在 2-64 个字符之间")
                return

            try:
                kb_data = {
                    "name": kb_name.strip(),
                    "description": description.strip() if description else "",
                    "embedding_model": embedding_model,
                    "embedding_dimension": embedding_dimension,
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
