"""UI 配置模块测试。

测试 rag5.interfaces.ui.config 模块的功能。
"""

import os
import pytest


class TestUIConfig:
    """测试 UIConfig 类"""

    def test_default_config_values(self):
        """测试默认配置值"""
        from rag5.interfaces.ui.config import UIConfig

        # 测试默认值（在没有环境变量时）
        # 注意：由于配置是在模块导入时读取的，这个测试只能验证当前值
        assert isinstance(UIConfig.API_BASE_URL, str)
        assert isinstance(UIConfig.API_TIMEOUT, int)
        assert isinstance(UIConfig.PAGE_SIZE, int)
        assert isinstance(UIConfig.FILE_PAGE_SIZE, int)
        assert isinstance(UIConfig.CACHE_TTL, int)

        # 验证默认值的合理性
        assert UIConfig.API_TIMEOUT > 0
        assert UIConfig.PAGE_SIZE > 0
        assert UIConfig.FILE_PAGE_SIZE > 0
        assert UIConfig.CACHE_TTL > 0

    def test_get_api_base_url(self):
        """测试获取 API 基础 URL"""
        from rag5.interfaces.ui.config import UIConfig

        url = UIConfig.get_api_base_url()
        assert isinstance(url, str)
        assert url  # 不为空

    def test_get_api_timeout(self):
        """测试获取 API 超时时间"""
        from rag5.interfaces.ui.config import UIConfig

        timeout = UIConfig.get_api_timeout()
        assert isinstance(timeout, int)
        assert timeout > 0

    def test_get_page_size(self):
        """测试获取页面大小"""
        from rag5.interfaces.ui.config import UIConfig

        page_size = UIConfig.get_page_size()
        assert isinstance(page_size, int)
        assert page_size > 0

    def test_get_file_page_size(self):
        """测试获取文件页面大小"""
        from rag5.interfaces.ui.config import UIConfig

        file_page_size = UIConfig.get_file_page_size()
        assert isinstance(file_page_size, int)
        assert file_page_size > 0

    def test_get_cache_ttl(self):
        """测试获取缓存 TTL"""
        from rag5.interfaces.ui.config import UIConfig

        cache_ttl = UIConfig.get_cache_ttl()
        assert isinstance(cache_ttl, int)
        assert cache_ttl > 0

    def test_display_config(self):
        """测试显示配置"""
        from rag5.interfaces.ui.config import UIConfig

        config_dict = UIConfig.display_config()
        assert isinstance(config_dict, dict)

        # 验证结构
        assert "api" in config_dict
        assert "ui" in config_dict
        assert "cache" in config_dict

        # 验证 API 配置
        assert "base_url" in config_dict["api"]
        assert "timeout" in config_dict["api"]

        # 验证 UI 配置
        assert "page_size" in config_dict["ui"]
        assert "file_page_size" in config_dict["ui"]

        # 验证缓存配置
        assert "ttl" in config_dict["cache"]

    def test_global_config_instance(self):
        """测试全局配置实例"""
        from rag5.interfaces.ui.config import config

        # 验证全局实例可以访问所有配置
        assert hasattr(config, "API_BASE_URL")
        assert hasattr(config, "API_TIMEOUT")
        assert hasattr(config, "PAGE_SIZE")
        assert hasattr(config, "FILE_PAGE_SIZE")
        assert hasattr(config, "CACHE_TTL")

    def test_config_types(self):
        """测试配置类型正确性"""
        from rag5.interfaces.ui.config import UIConfig

        # 验证类型
        assert isinstance(UIConfig.API_BASE_URL, str)
        assert isinstance(UIConfig.API_TIMEOUT, int)
        assert isinstance(UIConfig.PAGE_SIZE, int)
        assert isinstance(UIConfig.FILE_PAGE_SIZE, int)
        assert isinstance(UIConfig.CACHE_TTL, int)

    def test_config_values_reasonable(self):
        """测试配置值合理性"""
        from rag5.interfaces.ui.config import UIConfig

        # 验证值的合理范围
        assert 0 < UIConfig.API_TIMEOUT <= 300  # 超时时间应在合理范围
        assert 1 <= UIConfig.PAGE_SIZE <= 100  # 页面大小应在合理范围
        assert 1 <= UIConfig.FILE_PAGE_SIZE <= 100  # 文件页面大小应在合理范围
        assert 0 < UIConfig.CACHE_TTL <= 3600  # 缓存 TTL 应在合理范围
