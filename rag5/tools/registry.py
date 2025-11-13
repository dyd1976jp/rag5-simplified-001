"""
工具注册器模块

提供工具注册和管理功能，允许动态添加和获取工具。
"""

from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册器

    管理所有可用的工具，提供注册、查询和获取工具的功能。

    示例:
        >>> from rag5.tools.registry import tool_registry
        >>>
        >>> # 注册工具
        >>> tool_registry.register(my_tool)
        >>>
        >>> # 获取所有工具
        >>> all_tools = tool_registry.get_all()
        >>>
        >>> # 按名称获取工具
        >>> tool = tool_registry.get_by_name("search_knowledge_base")
    """

    def __init__(self):
        """初始化工具注册器"""
        self._tools: Dict[str, Any] = {}
        logger.debug("初始化工具注册器")

    def register(self, tool: Any, name: Optional[str] = None) -> None:
        """
        注册工具

        参数:
            tool: 要注册的工具对象或函数
            name: 工具名称（可选）。如果未提供，将尝试从工具对象获取

        异常:
            ValueError: 如果工具名称为空或工具已存在

        示例:
            >>> tool_registry.register(search_tool, "search")
            >>> tool_registry.register(my_tool)  # 使用工具自身的名称
        """
        # 获取工具名称
        if name is None:
            # 尝试从工具对象获取名称
            if hasattr(tool, 'name'):
                name = tool.name
            elif hasattr(tool, '__name__'):
                name = tool.__name__
            else:
                raise ValueError("无法确定工具名称，请提供 name 参数")

        if not name:
            raise ValueError("工具名称不能为空")

        # 检查是否已存在
        if name in self._tools:
            logger.warning(f"工具 '{name}' 已存在，将被覆盖")

        # 注册工具
        self._tools[name] = tool
        logger.info(f"✓ 注册工具: {name}")

    def unregister(self, name: str) -> bool:
        """
        注销工具

        参数:
            name: 要注销的工具名称

        返回:
            是否成功注销

        示例:
            >>> tool_registry.unregister("search")
            True
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"注销工具: {name}")
            return True
        else:
            logger.warning(f"工具 '{name}' 不存在")
            return False

    def get_by_name(self, name: str) -> Optional[Any]:
        """
        按名称获取工具

        参数:
            name: 工具名称

        返回:
            工具对象，如果不存在则返回 None

        示例:
            >>> tool = tool_registry.get_by_name("search_knowledge_base")
            >>> if tool:
            ...     result = tool.invoke({"query": "测试"})
        """
        tool = self._tools.get(name)
        if tool is None:
            logger.warning(f"工具 '{name}' 未找到")
        return tool

    def get_all(self) -> List[Any]:
        """
        获取所有已注册的工具

        返回:
            所有工具的列表

        示例:
            >>> tools = tool_registry.get_all()
            >>> print(f"共有 {len(tools)} 个工具")
        """
        return list(self._tools.values())

    def get_tool_names(self) -> List[str]:
        """
        获取所有工具名称

        返回:
            所有工具名称的列表

        示例:
            >>> names = tool_registry.get_tool_names()
            >>> print(f"可用工具: {', '.join(names)}")
        """
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """
        检查工具是否存在

        参数:
            name: 工具名称

        返回:
            工具是否存在

        示例:
            >>> if tool_registry.has_tool("search"):
            ...     print("搜索工具可用")
        """
        return name in self._tools

    def clear(self) -> None:
        """
        清空所有已注册的工具

        示例:
            >>> tool_registry.clear()
        """
        count = len(self._tools)
        self._tools.clear()
        logger.info(f"清空了 {count} 个工具")

    def __len__(self) -> int:
        """返回已注册工具的数量"""
        return len(self._tools)

    def __repr__(self) -> str:
        """返回注册器的字符串表示"""
        return f"<ToolRegistry(tools={len(self._tools)})>"

    def __str__(self) -> str:
        """返回注册器的可读字符串"""
        if not self._tools:
            return "ToolRegistry: 无已注册工具"
        tool_list = ", ".join(self._tools.keys())
        return f"ToolRegistry: {tool_list}"


# ============================================================================
# 全局工具注册器单例
# ============================================================================

tool_registry = ToolRegistry()
