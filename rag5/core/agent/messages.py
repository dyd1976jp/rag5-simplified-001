"""
消息处理模块

处理消息格式转换，包括字典格式和 LangChain 消息格式之间的相互转换。
"""

from typing import List, Dict, Any, Optional
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage
)

from rag5.utils.context_logger import ConversationContextLogger


class MessageProcessor:
    """
    消息处理器类

    负责在不同消息格式之间进行转换，以及从代理结果中提取响应。
    """

    def __init__(
        self,
        context_logger: Optional[ConversationContextLogger] = None
    ):
        """
        初始化消息处理器

        Args:
            context_logger: 可选的对话上下文日志记录器
        """
        self.context_logger = context_logger

    def dict_to_langchain(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        """
        将字典格式的消息转换为 LangChain 消息格式

        Args:
            messages: 字典格式的消息列表，格式为:
                     [{"role": "user", "content": "..."},
                      {"role": "assistant", "content": "..."},
                      {"role": "system", "content": "..."}]

        Returns:
            LangChain 消息对象列表

        Example:
            >>> processor = MessageProcessor()
            >>> dict_msgs = [
            ...     {"role": "user", "content": "你好"},
            ...     {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
            ... ]
            >>> lc_msgs = processor.dict_to_langchain(dict_msgs)
            >>> print(type(lc_msgs[0]))
            <class 'langchain_core.messages.human.HumanMessage'>
        """
        langchain_messages = []
        
        # Calculate total content length for logging
        total_content_length = sum(len(msg.get("content", "")) for msg in messages)

        for msg in messages:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")

            if role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant" or role == "ai":
                langchain_messages.append(AIMessage(content=content))
            elif role == "system":
                langchain_messages.append(SystemMessage(content=content))
            else:
                # 默认作为人类消息处理
                langchain_messages.append(HumanMessage(content=content))
        
        # Log context information if logger is available
        if self.context_logger and messages:
            # Estimate tokens (rough approximation: 1 token ≈ 4 characters for English, 1.5 for Chinese)
            # Using conservative estimate of 2 characters per token
            estimated_tokens = total_content_length // 2
            
            # Log the conversion with message count and content length
            self.context_logger.log_message_added(
                role="batch_conversion",
                content_length=total_content_length,
                total_messages=len(messages),
                total_tokens=estimated_tokens
            )

        return langchain_messages

    def langchain_to_dict(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """
        将 LangChain 消息格式转换为字典格式

        Args:
            messages: LangChain 消息对象列表

        Returns:
            字典格式的消息列表

        Example:
            >>> from langchain_core.messages import HumanMessage, AIMessage
            >>> processor = MessageProcessor()
            >>> lc_msgs = [
            ...     HumanMessage(content="你好"),
            ...     AIMessage(content="你好！有什么可以帮助你的吗？")
            ... ]
            >>> dict_msgs = processor.langchain_to_dict(lc_msgs)
            >>> print(dict_msgs[0])
            {'role': 'user', 'content': '你好'}
        """
        dict_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                dict_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                dict_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                dict_messages.append({"role": "system", "content": msg.content})
            else:
                # 未知类型，尝试获取内容
                dict_messages.append({"role": "unknown", "content": str(msg.content)})

        return dict_messages

    def extract_ai_response(self, result: Dict[str, Any]) -> str:
        """
        从代理执行结果中提取 AI 响应

        Args:
            result: 代理执行返回的结果字典，通常包含 "messages" 键

        Returns:
            提取的 AI 响应文本，如果未找到则返回默认消息

        Example:
            >>> from langchain_core.messages import AIMessage
            >>> processor = MessageProcessor()
            >>> result = {
            ...     "messages": [
            ...         AIMessage(content="这是回答")
            ...     ]
            ... }
            >>> response = processor.extract_ai_response(result)
            >>> print(response)
            这是回答
        """
        answer = ""

        # 检查结果中是否包含 messages
        if "messages" in result and result["messages"]:
            # 从后向前查找最后一条 AI 消息
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    answer = msg.content
                    break

        # 如果没有找到答案，返回默认消息
        if not answer:
            answer = "抱歉，我无法生成回答。"

        return answer

    def format_chat_history(self, messages: List[Dict[str, str]]) -> str:
        """
        将对话历史格式化为文本字符串

        Args:
            messages: 字典格式的消息列表

        Returns:
            格式化的对话历史文本

        Example:
            >>> processor = MessageProcessor()
            >>> history = [
            ...     {"role": "user", "content": "你好"},
            ...     {"role": "assistant", "content": "你好！"}
            ... ]
            >>> formatted = processor.format_chat_history(history)
            >>> print(formatted)
            用户: 你好
            助手: 你好！
        """
        formatted_lines = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                formatted_lines.append(f"用户: {content}")
            elif role == "assistant" or role == "ai":
                formatted_lines.append(f"助手: {content}")
            elif role == "system":
                formatted_lines.append(f"系统: {content}")

        return "\n".join(formatted_lines)
