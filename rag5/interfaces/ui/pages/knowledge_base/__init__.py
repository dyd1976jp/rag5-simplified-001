"""
知识库管理页面模块。

本模块包含知识库管理相关的页面组件。
"""

from rag5.interfaces.ui.pages.knowledge_base.api_client import (
    KnowledgeBaseAPIClient,
    APIError,
    APIConnectionError,
    APITimeoutError,
    APIHTTPError
)

from rag5.interfaces.ui.pages.knowledge_base.list import (
    render_kb_list_page,
    render_kb_card,
    show_delete_confirmation,
    render_create_kb_dialog,
    format_datetime
)

from rag5.interfaces.ui.pages.knowledge_base.detail import (
    render_kb_detail_page,
    render_kb_header,
    render_file_management_tab,
    render_kb_settings_tab,
    render_retrieval_test_tab
)

__all__ = [
    "KnowledgeBaseAPIClient",
    "APIError",
    "APIConnectionError",
    "APITimeoutError",
    "APIHTTPError",
    "render_kb_list_page",
    "render_kb_card",
    "show_delete_confirmation",
    "render_create_kb_dialog",
    "format_datetime",
    "render_kb_detail_page",
    "render_kb_header",
    "render_file_management_tab",
    "render_kb_settings_tab",
    "render_retrieval_test_tab"
]
