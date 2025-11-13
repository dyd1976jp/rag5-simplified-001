"""
配置加载器模块

负责从环境变量和 .env 文件加载配置。
"""

import os
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    配置加载器类

    从环境变量和 .env 文件加载配置值。

    示例:
        >>> loader = ConfigLoader()
        >>> loader.load_env_file('.env')
        >>> host = loader.get_env('OLLAMA_HOST', 'http://localhost:11434')
    """

    def __init__(self):
        """初始化配置加载器"""
        self._env_cache: Dict[str, str] = {}

    def load_env_file(self, path: str = '.env') -> Dict[str, str]:
        """
        从 .env 文件加载环境变量

        参数:
            path: .env 文件路径，默认为当前目录下的 .env

        返回:
            加载的环境变量字典

        示例:
            >>> loader = ConfigLoader()
            >>> env_vars = loader.load_env_file('.env')
            >>> print(env_vars.get('OLLAMA_HOST'))
        """
        env_vars = {}
        env_path = Path(path)

        if not env_path.exists():
            logger.warning(f".env 文件不存在: {path}")
            return env_vars

        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # 去除空白字符
                    line = line.strip()

                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue

                    # 解析键值对
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        # 移除值两端的引号
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]

                        env_vars[key] = value
                        # 同时设置到环境变量中（.env 文件优先）
                        os.environ[key] = value
                    else:
                        logger.warning(f".env 文件第 {line_num} 行格式错误: {line}")

            self._env_cache.update(env_vars)
            logger.info(f"成功从 {path} 加载 {len(env_vars)} 个配置项")

        except Exception as e:
            logger.error(f"加载 .env 文件失败: {e}")
            raise

        return env_vars

    def get_env(self, key: str, default: Optional[str] = None) -> str:
        """
        获取环境变量值

        首先从系统环境变量中查找，如果不存在则使用默认值。

        参数:
            key: 环境变量名称
            default: 默认值，如果环境变量不存在则返回此值

        返回:
            环境变量的值或默认值

        示例:
            >>> loader = ConfigLoader()
            >>> host = loader.get_env('OLLAMA_HOST', 'http://localhost:11434')
        """
        value = os.environ.get(key)

        if value is None:
            if default is not None:
                logger.debug(f"环境变量 {key} 未设置，使用默认值: {default}")
                return default
            else:
                logger.warning(f"环境变量 {key} 未设置且无默认值")
                return ""

        return value

    def get_env_int(self, key: str, default: int) -> int:
        """
        获取整数类型的环境变量

        参数:
            key: 环境变量名称
            default: 默认值

        返回:
            整数值
        """
        value = self.get_env(key)
        if not value:
            return default

        try:
            return int(value)
        except ValueError:
            logger.warning(f"环境变量 {key} 的值 '{value}' 不是有效的整数，使用默认值: {default}")
            return default

    def get_env_float(self, key: str, default: float) -> float:
        """
        获取浮点数类型的环境变量

        参数:
            key: 环境变量名称
            default: 默认值

        返回:
            浮点数值
        """
        value = self.get_env(key)
        if not value:
            return default

        try:
            return float(value)
        except ValueError:
            logger.warning(f"环境变量 {key} 的值 '{value}' 不是有效的浮点数，使用默认值: {default}")
            return default

    def get_env_bool(self, key: str, default: bool) -> bool:
        """
        获取布尔类型的环境变量

        参数:
            key: 环境变量名称
            default: 默认值

        返回:
            布尔值
        """
        value = self.get_env(key)
        if not value:
            return default

        return value.lower() in ('true', '1', 'yes', 'on')
