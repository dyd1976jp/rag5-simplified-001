"""UI 配置模块。

本模块提供 Streamlit UI 的配置管理，支持从环境变量读取配置。
"""

import os
from typing import Optional


class UIConfig:
    """UI 配置类。

    管理 Streamlit 应用的所有配置项，包括 API 连接、UI 显示、缓存等。
    所有配置都支持通过环境变量设置，如果环境变量不存在则使用默认值。

    属性:
        API_BASE_URL: API 后端服务的基础 URL
        API_TIMEOUT: API 请求超时时间（秒）
        PAGE_SIZE: 知识库列表每页显示数量
        FILE_PAGE_SIZE: 文件列表每页显示数量
        CACHE_TTL: 缓存存活时间（秒）

    示例:
        >>> config = UIConfig()
        >>> print(config.API_BASE_URL)
        http://localhost:8000
        >>> print(config.PAGE_SIZE)
        9
    """

    # API 配置
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))

    # UI 配置
    PAGE_SIZE: int = int(os.getenv("PAGE_SIZE", "9"))
    FILE_PAGE_SIZE: int = int(os.getenv("FILE_PAGE_SIZE", "10"))

    # 缓存配置
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "60"))

    @classmethod
    def get_api_base_url(cls) -> str:
        """获取 API 基础 URL。

        返回:
            API 基础 URL 字符串
        """
        return cls.API_BASE_URL

    @classmethod
    def get_api_timeout(cls) -> int:
        """获取 API 请求超时时间。

        返回:
            超时时间（秒）
        """
        return cls.API_TIMEOUT

    @classmethod
    def get_page_size(cls) -> int:
        """获取知识库列表每页显示数量。

        返回:
            每页显示数量
        """
        return cls.PAGE_SIZE

    @classmethod
    def get_file_page_size(cls) -> int:
        """获取文件列表每页显示数量。

        返回:
            每页显示数量
        """
        return cls.FILE_PAGE_SIZE

    @classmethod
    def get_cache_ttl(cls) -> int:
        """获取缓存存活时间。

        返回:
            缓存 TTL（秒）
        """
        return cls.CACHE_TTL

    @classmethod
    def display_config(cls) -> dict:
        """显示所有配置信息。

        返回:
            包含所有配置项的字典
        """
        return {
            "api": {
                "base_url": cls.API_BASE_URL,
                "timeout": cls.API_TIMEOUT,
            },
            "ui": {
                "page_size": cls.PAGE_SIZE,
                "file_page_size": cls.FILE_PAGE_SIZE,
            },
            "cache": {
                "ttl": cls.CACHE_TTL,
            },
        }


# 创建全局配置实例
config = UIConfig()
