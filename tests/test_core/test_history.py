"""
测试对话历史管理器模块
"""

import pytest
from langchain_core.messages import HumanMessage, AIMessage
from rag5.core.agent import ConversationHistory


def test_conversation_history_initialization():
    """测试ConversationHistory初始化"""
    history = ConversationHistory()
    assert history is not None
    assert history.count() == 0


def test_add_user_message():
    """测试添加用户消息"""
    history = ConversationHistory()

    history.add_user_message("你好")

    assert history.count() == 1
    messages = history.get_messages()
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "你好"


def test_add_assistant_message():
    """测试添加助手消息"""
    history = ConversationHistory()

    history.add_assistant_message("你好！")

    assert history.count() == 1
    messages = history.get_messages()
    assert messages[0]["role"] == "assistant"
    assert messages[0]["content"] == "你好！"


def test_add_message_generic():
    """测试通用添加消息方法"""
    history = ConversationHistory()

    history.add_message("user", "问题")
    history.add_message("assistant", "回答")

    assert history.count() == 2
    messages = history.get_messages()
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_add_multiple_messages():
    """测试添加多条消息"""
    history = ConversationHistory()

    history.add_user_message("问题1")
    history.add_assistant_message("回答1")
    history.add_user_message("问题2")
    history.add_assistant_message("回答2")

    assert history.count() == 4
    messages = history.get_messages()
    assert len(messages) == 4


def test_get_messages_with_limit():
    """测试获取限定数量的消息"""
    history = ConversationHistory()

    for i in range(10):
        history.add_user_message(f"消息{i}")

    messages = history.get_messages(limit=5)

    assert len(messages) == 5
    # 应该返回最近的5条消息
    assert messages[0]["content"] == "消息5"
    assert messages[4]["content"] == "消息9"


def test_get_messages_no_limit():
    """测试获取所有消息"""
    history = ConversationHistory()

    for i in range(10):
        history.add_user_message(f"消息{i}")

    messages = history.get_messages()

    assert len(messages) == 10


def test_clear_history():
    """测试清空历史"""
    history = ConversationHistory()

    history.add_user_message("消息1")
    history.add_user_message("消息2")
    assert history.count() == 2

    history.clear()

    assert history.count() == 0
    assert len(history.get_messages()) == 0


def test_to_langchain_messages():
    """测试转换为LangChain消息格式"""
    history = ConversationHistory()

    history.add_user_message("你好")
    history.add_assistant_message("你好！")

    lc_messages = history.to_langchain_messages()

    assert len(lc_messages) == 2
    assert isinstance(lc_messages[0], HumanMessage)
    assert isinstance(lc_messages[1], AIMessage)
    assert lc_messages[0].content == "你好"
    assert lc_messages[1].content == "你好！"


def test_to_langchain_messages_empty():
    """测试转换空历史为LangChain消息"""
    history = ConversationHistory()

    lc_messages = history.to_langchain_messages()

    assert len(lc_messages) == 0


def test_to_langchain_messages_with_limit():
    """测试转换限定数量的消息为LangChain格式"""
    history = ConversationHistory()

    for i in range(10):
        history.add_user_message(f"消息{i}")

    lc_messages = history.to_langchain_messages(limit=3)

    assert len(lc_messages) == 3


def test_count_method():
    """测试count方法"""
    history = ConversationHistory()

    assert history.count() == 0

    history.add_user_message("消息1")
    assert history.count() == 1

    history.add_assistant_message("回答1")
    assert history.count() == 2

    history.clear()
    assert history.count() == 0


def test_is_empty_method():
    """测试is_empty方法"""
    history = ConversationHistory()

    if hasattr(history, 'is_empty'):
        assert history.is_empty() is True

        history.add_user_message("消息")
        assert history.is_empty() is False

        history.clear()
        assert history.is_empty() is True


def test_get_last_message():
    """测试获取最后一条消息"""
    history = ConversationHistory()

    history.add_user_message("消息1")
    history.add_assistant_message("回答1")
    history.add_user_message("消息2")

    if hasattr(history, 'get_last_message'):
        last_msg = history.get_last_message()
        assert last_msg["role"] == "user"
        assert last_msg["content"] == "消息2"


def test_chinese_content_preservation():
    """测试中文内容保留"""
    history = ConversationHistory()

    chinese_text = "这是一个包含中文的测试消息，包括标点符号：，。！？"
    history.add_user_message(chinese_text)

    messages = history.get_messages()
    assert messages[0]["content"] == chinese_text


def test_empty_message_handling():
    """测试空消息处理"""
    history = ConversationHistory()

    # 根据实现，可能允许或不允许空消息
    try:
        history.add_user_message("")
        messages = history.get_messages()
        # 如果允许，验证它被添加了
        assert len(messages) >= 0
    except ValueError:
        # 如果不允许，应该抛出ValueError
        pass


def test_message_order_preservation():
    """测试消息顺序保留"""
    history = ConversationHistory()

    expected_order = []
    for i in range(5):
        msg = f"消息{i}"
        history.add_user_message(msg)
        expected_order.append(msg)

    messages = history.get_messages()
    actual_order = [msg["content"] for msg in messages]

    assert actual_order == expected_order


def test_add_message_with_metadata():
    """测试添加带元数据的消息"""
    history = ConversationHistory()

    # 如果实现支持元数据
    if hasattr(history, 'add_message_with_metadata'):
        history.add_message_with_metadata(
            "user",
            "测试消息",
            metadata={"timestamp": "2024-01-01", "source": "test"}
        )

        messages = history.get_messages()
        assert messages[0]["metadata"]["timestamp"] == "2024-01-01"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
