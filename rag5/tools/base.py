"""
工具基类模块

定义工具的基础接口和抽象类。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    工具基类

    所有自定义工具都应该继承此类并实现必要的方法。

    属性:
        name: 工具名称
        description: 工具描述

    示例:
        >>> class MyTool(BaseTool):
        ...     def __init__(self):
        ...         super().__init__(
        ...             name="my_tool",
        ...             description="这是我的工具"
        ...         )
        ...
        ...     def execute(self, **kwargs) -> Any:
        ...         return "执行结果"
    """

    def __init__(self, name: str, description: str):
        """
        初始化工具

        参数:
            name: 工具名称
            description: 工具描述
        """
        self.name = name
        self.description = description
        logger.debug(f"初始化工具: {name}")

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        执行工具

        参数:
            **kwargs: 工具执行所需的参数

        返回:
            工具执行结果

        异常:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现 execute 方法")

    def validate_params(self, **kwargs) -> bool:
        """
        验证参数

        参数:
            **kwargs: 需要验证的参数

        返回:
            参数是否有效
        """
        # 默认实现：不进行验证
        return True

    def __repr__(self) -> str:
        """返回工具的字符串表示"""
        return f"<{self.__class__.__name__}(name='{self.name}')>"

    def __str__(self) -> str:
        """返回工具的可读字符串"""
        return f"{self.name}: {self.description}"
