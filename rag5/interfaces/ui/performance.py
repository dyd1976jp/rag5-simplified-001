"""UI 性能优化模块。

本模块提供 Streamlit UI 的性能优化功能，包括缓存、懒加载等策略。
"""

import streamlit as st
from typing import Dict, Optional, Any
from rag5.interfaces.ui.config import config


# ============================================================================
# 缓存策略 / Caching Strategy
# ============================================================================


@st.cache_data(ttl=config.CACHE_TTL)
def get_knowledge_bases_cached(api_client) -> Dict[str, Any]:
    """缓存知识库列表。

    使用 Streamlit 的 cache_data 装饰器缓存知识库列表，减少 API 调用。
    缓存时间由配置中的 CACHE_TTL 决定（默认 60 秒）。

    参数:
        api_client: KnowledgeBaseAPIClient 实例

    返回:
        包含知识库列表的字典，格式：
        {
            "items": [...],
            "total": int,
            "pages": int
        }

    示例:
        >>> from rag5.interfaces.ui.pages.knowledge_base.api_client import KnowledgeBaseAPIClient
        >>> api_client = KnowledgeBaseAPIClient()
        >>> result = get_knowledge_bases_cached(api_client)
        >>> print(result["items"])
    """
    return api_client.list_knowledge_bases(page=1, size=100)


@st.cache_data(ttl=30)
def get_kb_files_cached(api_client, kb_id: str) -> Dict[str, Any]:
    """缓存文件列表。

    使用 Streamlit 的 cache_data 装饰器缓存文件列表，减少 API 调用。
    缓存时间为 30 秒（文件状态变化较快，使用较短的 TTL）。

    参数:
        api_client: KnowledgeBaseAPIClient 实例
        kb_id: 知识库 ID

    返回:
        包含文件列表的字典，格式：
        {
            "items": [...],
            "total": int,
            "pages": int
        }

    示例:
        >>> result = get_kb_files_cached(api_client, "kb_123")
        >>> print(result["items"])
    """
    return api_client.list_files(kb_id, page=1, size=100)


# ============================================================================
# 状态优化 / State Optimization
# ============================================================================


class StateOptimizer:
    """状态优化器。

    提供优化 Streamlit 状态管理和页面重载的工具方法。
    """

    @staticmethod
    def should_rerun(key: str) -> bool:
        """判断是否需要重新运行页面。

        通过检查 session_state 中的标志，避免不必要的 st.rerun() 调用。

        参数:
            key: 状态键名

        返回:
            是否需要重新运行

        示例:
            >>> if StateOptimizer.should_rerun("data_updated"):
            ...     st.rerun()
        """
        if key not in st.session_state:
            return False
        should_run = st.session_state.get(key, False)
        if should_run:
            # 重置标志
            st.session_state[key] = False
            return True
        return False

    @staticmethod
    def mark_for_rerun(key: str):
        """标记需要重新运行页面。

        设置 session_state 标志，指示下次需要重新运行页面。

        参数:
            key: 状态键名

        示例:
            >>> StateOptimizer.mark_for_rerun("data_updated")
        """
        st.session_state[key] = True

    @staticmethod
    def cache_api_response(key: str, response: Any):
        """在 session_state 中缓存 API 响应。

        将 API 响应存储在 session_state 中，避免重复调用。

        参数:
            key: 缓存键名
            response: API 响应数据

        示例:
            >>> StateOptimizer.cache_api_response("kb_list", response)
        """
        cache_key = f"_cache_{key}"
        st.session_state[cache_key] = response

    @staticmethod
    def get_cached_response(key: str) -> Optional[Any]:
        """从 session_state 获取缓存的 API 响应。

        参数:
            key: 缓存键名

        返回:
            缓存的响应数据，如果不存在则返回 None

        示例:
            >>> cached = StateOptimizer.get_cached_response("kb_list")
            >>> if cached is None:
            ...     cached = api_client.list_knowledge_bases()
        """
        cache_key = f"_cache_{key}"
        return st.session_state.get(cache_key, None)

    @staticmethod
    def clear_cache(key: Optional[str] = None):
        """清除缓存的 API 响应。

        参数:
            key: 缓存键名，如果为 None 则清除所有缓存

        示例:
            >>> StateOptimizer.clear_cache("kb_list")  # 清除特定缓存
            >>> StateOptimizer.clear_cache()  # 清除所有缓存
        """
        if key is None:
            # 清除所有缓存
            cache_keys = [k for k in st.session_state.keys() if k.startswith("_cache_")]
            for cache_key in cache_keys:
                del st.session_state[cache_key]
        else:
            cache_key = f"_cache_{key}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]


# ============================================================================
# 懒加载策略 / Lazy Loading Strategy
# ============================================================================


class LazyLoader:
    """懒加载器。

    提供懒加载功能，按需加载数据以提升性能。
    """

    @staticmethod
    def should_load_page(current_page: int, loaded_pages: set) -> bool:
        """判断是否需要加载指定页面。

        参数:
            current_page: 当前页码
            loaded_pages: 已加载的页码集合

        返回:
            是否需要加载

        示例:
            >>> loaded = set()
            >>> if LazyLoader.should_load_page(2, loaded):
            ...     # 加载第 2 页数据
            ...     loaded.add(2)
        """
        return current_page not in loaded_pages

    @staticmethod
    def mark_page_loaded(page: int, loaded_pages: set):
        """标记页面已加载。

        参数:
            page: 页码
            loaded_pages: 已加载的页码集合

        示例:
            >>> loaded = set()
            >>> LazyLoader.mark_page_loaded(1, loaded)
        """
        loaded_pages.add(page)

    @staticmethod
    def get_loaded_pages_key(prefix: str) -> str:
        """获取已加载页面的 session_state 键名。

        参数:
            prefix: 键名前缀

        返回:
            完整的键名

        示例:
            >>> key = LazyLoader.get_loaded_pages_key("kb_list")
            >>> loaded = st.session_state.get(key, set())
        """
        return f"_loaded_pages_{prefix}"

    @staticmethod
    def init_loaded_pages(prefix: str):
        """初始化已加载页面集合。

        参数:
            prefix: 键名前缀

        示例:
            >>> LazyLoader.init_loaded_pages("kb_list")
        """
        key = LazyLoader.get_loaded_pages_key(prefix)
        if key not in st.session_state:
            st.session_state[key] = set()


# ============================================================================
# 性能监控 / Performance Monitoring
# ============================================================================


class PerformanceMonitor:
    """性能监控器。

    提供简单的性能监控功能，用于识别性能瓶颈。
    """

    @staticmethod
    def log_cache_hit(key: str):
        """记录缓存命中。

        参数:
            key: 缓存键名

        示例:
            >>> PerformanceMonitor.log_cache_hit("kb_list")
        """
        stats_key = "_perf_cache_hits"
        if stats_key not in st.session_state:
            st.session_state[stats_key] = {}
        if key not in st.session_state[stats_key]:
            st.session_state[stats_key][key] = 0
        st.session_state[stats_key][key] += 1

    @staticmethod
    def log_cache_miss(key: str):
        """记录缓存未命中。

        参数:
            key: 缓存键名

        示例:
            >>> PerformanceMonitor.log_cache_miss("kb_list")
        """
        stats_key = "_perf_cache_misses"
        if stats_key not in st.session_state:
            st.session_state[stats_key] = {}
        if key not in st.session_state[stats_key]:
            st.session_state[stats_key][key] = 0
        st.session_state[stats_key][key] += 1

    @staticmethod
    def get_cache_stats() -> Dict[str, Dict[str, int]]:
        """获取缓存统计信息。

        返回:
            包含缓存命中和未命中统计的字典

        示例:
            >>> stats = PerformanceMonitor.get_cache_stats()
            >>> print(stats["hits"])
            >>> print(stats["misses"])
        """
        return {
            "hits": st.session_state.get("_perf_cache_hits", {}),
            "misses": st.session_state.get("_perf_cache_misses", {}),
        }
