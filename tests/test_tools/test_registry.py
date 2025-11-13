"""
测试工具注册器模块
"""

import pytest
from unittest.mock import Mock
from rag5.tools.registry import ToolRegistry


def test_registry_initialization():
    """测试ToolRegistry初始化"""
    registry = ToolRegistry()
    assert registry is not None
    assert len(registry.get_all()) == 0


def test_register_tool():
    """测试注册工具"""
    registry = ToolRegistry()

    mock_tool = Mock()
    mock_tool.name = "test_tool"
    mock_tool.description = "测试工具"

    registry.register(mock_tool)

    assert len(registry.get_all()) == 1
    assert registry.get_by_name("test_tool") == mock_tool


def test_register_multiple_tools():
    """测试注册多个工具"""
    registry = ToolRegistry()

    tools = []
    for i in range(3):
        mock_tool = Mock()
        mock_tool.name = f"tool_{i}"
        mock_tool.description = f"工具 {i}"
        tools.append(mock_tool)
        registry.register(mock_tool)

    assert len(registry.get_all()) == 3

    for i, tool in enumerate(tools):
        assert registry.get_by_name(f"tool_{i}") == tool


def test_get_by_name_not_found():
    """测试获取不存在的工具"""
    registry = ToolRegistry()

    result = registry.get_by_name("nonexistent_tool")
    assert result is None


def test_register_duplicate_tool():
    """测试注册重复工具（应该覆盖）"""
    registry = ToolRegistry()

    tool1 = Mock()
    tool1.name = "duplicate_tool"
    tool1.description = "第一个工具"

    tool2 = Mock()
    tool2.name = "duplicate_tool"
    tool2.description = "第二个工具"

    registry.register(tool1)
    registry.register(tool2)

    # 应该只有一个工具
    assert len(registry.get_all()) == 1
    # 应该是第二个工具
    assert registry.get_by_name("duplicate_tool") == tool2


def test_get_all_returns_list():
    """测试get_all返回列表"""
    registry = ToolRegistry()

    tools = registry.get_all()
    assert isinstance(tools, list)


def test_global_registry():
    """测试全局注册器单例"""
    from rag5.tools.registry import tool_registry

    assert tool_registry is not None
    assert isinstance(tool_registry, ToolRegistry)


def test_registry_clear():
    """测试清空注册器"""
    registry = ToolRegistry()

    mock_tool = Mock()
    mock_tool.name = "test_tool"
    registry.register(mock_tool)

    assert len(registry.get_all()) == 1

    # 清空（如果实现了clear方法）
    if hasattr(registry, 'clear'):
        registry.clear()
        assert len(registry.get_all()) == 0


def test_registry_tool_names():
    """测试获取所有工具名称"""
    registry = ToolRegistry()

    for i in range(3):
        mock_tool = Mock()
        mock_tool.name = f"tool_{i}"
        registry.register(mock_tool)

    if hasattr(registry, 'get_tool_names'):
        names = registry.get_tool_names()
        assert len(names) == 3
        assert "tool_0" in names
        assert "tool_1" in names
        assert "tool_2" in names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
