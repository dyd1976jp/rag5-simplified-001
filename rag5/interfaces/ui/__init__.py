"""
UI 接口模块。

本模块提供基于 Streamlit 的 Web 用户界面，包括会话状态管理和 UI 组件。

使用示例：
    from rag5.interfaces.ui.app import main
    from rag5.interfaces.ui.state import SessionState
"""

# 使用延迟导入以避免在不需要时加载 Streamlit
# 用户应该直接从子模块导入需要的组件

__all__ = [
    'app',
    'state',
    'components',
]
