"""UI 性能优化模块测试。

测试 rag5.interfaces.ui.performance 模块的功能。
"""

import pytest


class TestStateOptimizer:
    """测试 StateOptimizer 类"""

    def setup_method(self):
        """每个测试前的设置"""
        # 清理 streamlit session_state
        try:
            import streamlit as st
            # 清理所有测试相关的状态
            keys_to_remove = [k for k in st.session_state.keys() if k.startswith("_test_")]
            for key in keys_to_remove:
                del st.session_state[key]
        except ImportError:
            # Streamlit 未安装，跳过
            pass

    def test_should_rerun_not_exists(self):
        """测试键不存在时不应重新运行"""
        from rag5.interfaces.ui.performance import StateOptimizer

        result = StateOptimizer.should_rerun("_test_nonexistent")
        assert result is False

    def test_mark_and_check_rerun(self):
        """测试标记和检查重新运行"""
        from rag5.interfaces.ui.performance import StateOptimizer

        # 标记需要重新运行
        StateOptimizer.mark_for_rerun("_test_rerun_key")

        # 第一次检查应该返回 True
        result = StateOptimizer.should_rerun("_test_rerun_key")
        assert result is True

        # 第二次检查应该返回 False（标志已重置）
        result = StateOptimizer.should_rerun("_test_rerun_key")
        assert result is False

    def test_cache_api_response(self):
        """测试缓存 API 响应"""
        from rag5.interfaces.ui.performance import StateOptimizer

        test_data = {"items": [1, 2, 3], "total": 3}

        # 缓存响应
        StateOptimizer.cache_api_response("_test_api", test_data)

        # 获取缓存
        cached = StateOptimizer.get_cached_response("_test_api")
        assert cached == test_data

    def test_get_cached_response_not_exists(self):
        """测试获取不存在的缓存"""
        from rag5.interfaces.ui.performance import StateOptimizer

        result = StateOptimizer.get_cached_response("_test_nonexistent_cache")
        assert result is None

    def test_clear_specific_cache(self):
        """测试清除特定缓存"""
        from rag5.interfaces.ui.performance import StateOptimizer

        # 设置缓存
        StateOptimizer.cache_api_response("_test_cache1", {"data": 1})
        StateOptimizer.cache_api_response("_test_cache2", {"data": 2})

        # 清除特定缓存
        StateOptimizer.clear_cache("_test_cache1")

        # 验证
        assert StateOptimizer.get_cached_response("_test_cache1") is None
        assert StateOptimizer.get_cached_response("_test_cache2") == {"data": 2}

    def test_clear_all_cache(self):
        """测试清除所有缓存"""
        from rag5.interfaces.ui.performance import StateOptimizer

        # 设置多个缓存
        StateOptimizer.cache_api_response("_test_cache1", {"data": 1})
        StateOptimizer.cache_api_response("_test_cache2", {"data": 2})

        # 清除所有缓存
        StateOptimizer.clear_cache()

        # 验证
        assert StateOptimizer.get_cached_response("_test_cache1") is None
        assert StateOptimizer.get_cached_response("_test_cache2") is None


class TestLazyLoader:
    """测试 LazyLoader 类"""

    def test_should_load_page_empty_set(self):
        """测试空集合时应该加载"""
        from rag5.interfaces.ui.performance import LazyLoader

        loaded = set()
        result = LazyLoader.should_load_page(1, loaded)
        assert result is True

    def test_should_load_page_already_loaded(self):
        """测试已加载的页面不应再加载"""
        from rag5.interfaces.ui.performance import LazyLoader

        loaded = {1, 2, 3}
        result = LazyLoader.should_load_page(2, loaded)
        assert result is False

    def test_mark_page_loaded(self):
        """测试标记页面已加载"""
        from rag5.interfaces.ui.performance import LazyLoader

        loaded = set()
        LazyLoader.mark_page_loaded(1, loaded)
        assert 1 in loaded

        LazyLoader.mark_page_loaded(2, loaded)
        assert 2 in loaded
        assert len(loaded) == 2

    def test_get_loaded_pages_key(self):
        """测试获取已加载页面键名"""
        from rag5.interfaces.ui.performance import LazyLoader

        key = LazyLoader.get_loaded_pages_key("kb_list")
        assert key == "_loaded_pages_kb_list"

        key = LazyLoader.get_loaded_pages_key("file_list")
        assert key == "_loaded_pages_file_list"

    def test_init_loaded_pages(self):
        """测试初始化已加载页面集合"""
        from rag5.interfaces.ui.performance import LazyLoader
        import streamlit as st

        prefix = "_test_lazy_load"
        LazyLoader.init_loaded_pages(prefix)

        key = LazyLoader.get_loaded_pages_key(prefix)
        assert key in st.session_state
        assert isinstance(st.session_state[key], set)
        assert len(st.session_state[key]) == 0


class TestPerformanceMonitor:
    """测试 PerformanceMonitor 类"""

    def setup_method(self):
        """每个测试前的设置"""
        # 清理性能统计
        try:
            import streamlit as st
            if "_perf_cache_hits" in st.session_state:
                del st.session_state["_perf_cache_hits"]
            if "_perf_cache_misses" in st.session_state:
                del st.session_state["_perf_cache_misses"]
        except ImportError:
            pass

    def test_log_cache_hit(self):
        """测试记录缓存命中"""
        from rag5.interfaces.ui.performance import PerformanceMonitor

        PerformanceMonitor.log_cache_hit("test_key")
        stats = PerformanceMonitor.get_cache_stats()
        assert "test_key" in stats["hits"]
        assert stats["hits"]["test_key"] == 1

        # 再次记录
        PerformanceMonitor.log_cache_hit("test_key")
        stats = PerformanceMonitor.get_cache_stats()
        assert stats["hits"]["test_key"] == 2

    def test_log_cache_miss(self):
        """测试记录缓存未命中"""
        from rag5.interfaces.ui.performance import PerformanceMonitor

        PerformanceMonitor.log_cache_miss("test_key")
        stats = PerformanceMonitor.get_cache_stats()
        assert "test_key" in stats["misses"]
        assert stats["misses"]["test_key"] == 1

        # 再次记录
        PerformanceMonitor.log_cache_miss("test_key")
        stats = PerformanceMonitor.get_cache_stats()
        assert stats["misses"]["test_key"] == 2

    def test_get_cache_stats_empty(self):
        """测试获取空的缓存统计"""
        from rag5.interfaces.ui.performance import PerformanceMonitor

        stats = PerformanceMonitor.get_cache_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert isinstance(stats["hits"], dict)
        assert isinstance(stats["misses"], dict)

    def test_multiple_keys_stats(self):
        """测试多个键的统计"""
        from rag5.interfaces.ui.performance import PerformanceMonitor

        PerformanceMonitor.log_cache_hit("key1")
        PerformanceMonitor.log_cache_hit("key2")
        PerformanceMonitor.log_cache_miss("key1")

        stats = PerformanceMonitor.get_cache_stats()
        assert stats["hits"]["key1"] == 1
        assert stats["hits"]["key2"] == 1
        assert stats["misses"]["key1"] == 1
