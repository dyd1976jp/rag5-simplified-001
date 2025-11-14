"""
对话历史管理模块

管理对话历史记录，包括添加、获取、清空消息等操作。
"""

from typing import List, Dict, Optional
from langchain_core.messages import BaseMessage

from rag5.core.agent.messages import MessageProcessor


class ConversationHistory:
    """
    对话历史管理器

    负责管理对话历史记录，支持添加、获取、清空消息，
    以及转换为 LangChain 消息格式。
    """

    def __init__(self):
        """初始化对话历史管理器"""
        self._messages: List[Dict[str, str]] = []
        self._message_processor = MessageProcessor()

    def add_message(self, role: str, content: str) -> None:
        """
        添加一条消息到历史记录

        Args:
            role: 消息角色，可以是 "user", "assistant", "system"
            content: 消息内容

        Example:
            >>> history = ConversationHistory()
            >>> history.add_message("user", "你好")
            >>> history.add_message("assistant", "你好！有什么可以帮助你的吗？")
            >>> print(len(history.get_messages()))
            2
        """
        if not content or not content.strip():
            return

        self._messages.append({
            "role": role,
            "content": content
        })

    def add_user_message(self, content: str) -> None:
        """
        添加用户消息的便捷方法

        Args:
            content: 消息内容
        """
        self.add_message("user", content)

    def add_assistant_message(self, content: str) -> None:
        """
        添加助手消息的便捷方法

        Args:
            content: 消息内容
        """
        self.add_message("assistant", content)

    def add_system_message(self, content: str) -> None:
        """
        添加系统消息的便捷方法

        Args:
            content: 消息内容
        """
        self.add_message("system", content)

    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        获取历史消息

        Args:
            limit: 可选，限制返回的消息数量。如果为 None，返回所有消息。
                  如果为正数，返回最近的 N 条消息。

        Returns:
            消息列表，格式为 [{"role": "user", "content": "..."}, ...]

        Example:
            >>> history = ConversationHistory()
            >>> history.add_message("user", "第一条消息")
            >>> history.add_message("assistant", "第一条回复")
            >>> history.add_message("user", "第二条消息")
            >>> messages = history.get_messages(limit=2)
            >>> print(len(messages))
            2
            >>> print(messages[0]["content"])
            第一条回复
        """
        if limit is None or limit <= 0:
            return self._messages.copy()

        # 返回最近的 N 条消息
        return self._messages[-limit:] if len(self._messages) > limit else self._messages.copy()

    def get_last_message(self) -> Optional[Dict[str, str]]:
        """
        获取最后一条消息

        Returns:
            最后一条消息，如果历史为空则返回 None

        Example:
            >>> history = ConversationHistory()
            >>> history.add_message("user", "你好")
            >>> last = history.get_last_message()
            >>> print(last["content"])
            你好
        """
        return self._messages[-1] if self._messages else None

    def clear(self) -> None:
        """
        清空所有历史消息

        Example:
            >>> history = ConversationHistory()
            >>> history.add_message("user", "你好")
            >>> history.clear()
            >>> print(len(history.get_messages()))
            0
        """
        self._messages.clear()

    def to_langchain_messages(self, limit: Optional[int] = None) -> List[BaseMessage]:
        """
        将历史消息转换为 LangChain 消息格式

        Args:
            limit: 可选，限制转换的消息数量

        Returns:
            LangChain 消息对象列表

        Example:
            >>> history = ConversationHistory()
            >>> history.add_message("user", "你好")
            >>> history.add_message("assistant", "你好！")
            >>> lc_messages = history.to_langchain_messages()
            >>> print(len(lc_messages))
            2
        """
        messages = self.get_messages(limit)
        return self._message_processor.dict_to_langchain(messages)

    def count(self) -> int:
        """
        获取历史消息数量

        Returns:
            消息数量

        Example:
            >>> history = ConversationHistory()
            >>> history.add_message("user", "你好")
            >>> print(history.count())
            1
        """
        return len(self._messages)

    def is_empty(self) -> bool:
        """
        检查历史是否为空

        Returns:
            如果历史为空返回 True，否则返回 False

        Example:
            >>> history = ConversationHistory()
            >>> print(history.is_empty())
            True
            >>> history.add_message("user", "你好")
            >>> print(history.is_empty())
            False
        """
        return len(self._messages) == 0

    def format_history(self) -> str:
        """
        将历史格式化为文本字符串

        Returns:
            格式化的历史文本

        Example:
            >>> history = ConversationHistory()
            >>> history.add_message("user", "你好")
            >>> history.add_message("assistant", "你好！")
            >>> print(history.format_history())
            用户: 你好
            助手: 你好！
        """
        return self._message_processor.format_chat_history(self._messages)
