"""
配置模块

提供统一的配置加载、验证和访问接口。

主要组件：
- settings: 全局配置单例，提供所有配置项的访问
- Settings: 配置类，可用于创建自定义配置实例
- ConfigLoader: 配置加载器，从环境变量加载配置
- ConfigValidator: 配置验证器，验证配置值的有效性
- defaults: 所有配置项的默认值

使用示例：
    # 基本使用 - 访问全局配置
    from rag5.config import settings
    print(settings.ollama_host)
    print(settings.llm_model)

    # 验证配置
    settings.validate()

    # 打印配置
    settings.print_config()

    # 高级使用 - 创建自定义配置实例
    from rag5.config import Settings
    custom_settings = Settings(env_file='.env.test')
"""

from rag5.config.settings import settings, Settings
from rag5.config.loader import ConfigLoader
from rag5.config.validator import ConfigValidator
from rag5.config import defaults

__all__ = [
    # 主要接口
    'settings',      # 全局配置单例（推荐使用）
    'Settings',      # 配置类（高级用法）

    # 组件（高级用法）
    'ConfigLoader',
    'ConfigValidator',
    'defaults',
]
