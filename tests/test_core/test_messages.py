"""
测试消息处理器模块
"""

import pytest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from rag5.core.agent import MessageProcessor


def test_message_processor_initialization():
    """测试MessageProcessor初始化"""
    processor = MessageProcessor()
    assert processor is not None


def test_dict_to_langchain_user_message():
    """测试字典转LangChain消息（用户消息）"""
    processor = MessageProcessor()

    dict_msgs = [{"role": "user", "content": "你好"}]
    lc_msgs = processor.dict_to_langchain(dict_msgs)

    assert len(lc_msgs) == 1
    assert isinstance(lc_msgs[0], HumanMessage)
    assert lc_msgs[0].content == "你好"


def test_dict_to_langchain_assistant_message():
    """测试字典转LangChain消息（助手消息）"""
    processor = MessageProcessor()

    dict_msgs = [{"role": "assistant", "content": "你好！"}]
    lc_msgs = processor.dict_to_langchain(dict_msgs)

    assert len(lc_msgs) == 1
    assert isinstance(lc_msgs[0], AIMessage)
    assert lc_msgs[0].content == "你好！"


def test_dict_to_langchain_system_message():
    """测试字典转LangChain消息（系统消息）"""
    processor = MessageProcessor()

    dict_msgs = [{"role": "system", "content": "你是一个助手"}]
    lc_msgs = processor.dict_to_langchain(dict_msgs)

    assert len(lc_msgs) == 1
    assert isinstance(lc_msgs[0], SystemMessage)
    assert lc_msgs[0].content == "你是一个助手"


def test_dict_to_langchain_multiple_messages():
    """测试字典转LangChain消息（多条消息）"""
    processor = MessageProcessor()

    dict_msgs = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
        {"role": "user", "content": "告诉我天气"}
    ]
    lc_msgs = processor.dict_to_langchain(dict_msgs)

    assert len(lc_msgs) == 3
    assert isinstance(lc_msgs[0], HumanMessage)
    assert isinstance(lc_msgs[1], AIMessage)
    assert isinstance(lc_msgs[2], HumanMessage)


def test_dict_to_langchain_empty_list():
    """测试字典转LangChain消息（空列表）"""
    processor = MessageProcessor()

    lc_msgs = processor.dict_to_langchain([])
    assert len(lc_msgs) == 0


def test_dict_to_langchain_invalid_role():
    """测试字典转LangChain消息（无效角色）"""
    processor = MessageProcessor()

    dict_msgs = [{"role": "invalid", "content": "测试"}]

    with pytest.raises(ValueError, match="Unknown role"):
        processor.dict_to_langchain(dict_msgs)


def test_langchain_to_dict_human_message():
    """测试LangChain消息转字典（用户消息）"""
    processor = MessageProcessor()

    lc_msgs = [HumanMessage(content="你好")]
    dict_msgs = processor.langchain_to_dict(lc_msgs)

    assert len(dict_msgs) == 1
    assert dict_msgs[0]["role"] == "user"
    assert dict_msgs[0]["content"] == "你好"


def test_langchain_to_dict_ai_message():
    """测试LangChain消息转字典（AI消息）"""
    processor = MessageProcessor()

    lc_msgs = [AIMessage(content="你好！")]
    dict_msgs = processor.langchain_to_dict(lc_msgs)

    assert len(dict_msgs) == 1
    assert dict_msgs[0]["role"] == "assistant"
    assert dict_msgs[0]["content"] == "你好！"


def test_langchain_to_dict_system_message():
    """测试LangChain消息转字典（系统消息）"""
    processor = MessageProcessor()

    lc_msgs = [SystemMessage(content="系统提示")]
    dict_msgs = processor.langchain_to_dict(lc_msgs)

    assert len(dict_msgs) == 1
    assert dict_msgs[0]["role"] == "system"
    assert dict_msgs[0]["content"] == "系统提示"


def test_langchain_to_dict_multiple_messages():
    """测试LangChain消息转字典（多条消息）"""
    processor = MessageProcessor()

    lc_msgs = [
        HumanMessage(content="问题1"),
        AIMessage(content="回答1"),
        HumanMessage(content="问题2")
    ]
    dict_msgs = processor.langchain_to_dict(lc_msgs)

    assert len(dict_msgs) == 3
    assert dict_msgs[0]["role"] == "user"
    assert dict_msgs[1]["role"] == "assistant"
    assert dict_msgs[2]["role"] == "user"


def test_extract_ai_response_simple():
    """测试提取AI响应（简单情况）"""
    processor = MessageProcessor()

    result = {
        "messages": [AIMessage(content="这是回答")]
    }

    response = processor.extract_ai_response(result)
    assert response == "这是回答"


def test_extract_ai_response_multiple_messages():
    """测试提取AI响应（多条消息）"""
    processor = MessageProcessor()

    result = {
        "messages": [
            HumanMessage(content="问题"),
            AIMessage(content="这是回答")
        ]
    }

    response = processor.extract_ai_response(result)
    assert response == "这是回答"


def test_extract_ai_response_no_ai_message():
    """测试提取AI响应（无AI消息）"""
    processor = MessageProcessor()

    result = {
        "messages": [HumanMessage(content="问题")]
    }

    response = processor.extract_ai_response(result)
    assert response == ""


def test_extract_ai_response_empty_messages():
    """测试提取AI响应（空消息列表）"""
    processor = MessageProcessor()

    result = {"messages": []}

    response = processor.extract_ai_response(result)
    assert response == ""


def test_extract_ai_response_no_messages_key():
    """测试提取AI响应（无messages键）"""
    processor = MessageProcessor()

    result = {}

    response = processor.extract_ai_response(result)
    assert response == ""


def test_round_trip_conversion():
    """测试往返转换"""
    processor = MessageProcessor()

    original_dict = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！"},
    ]

    # 字典 -> LangChain -> 字典
    lc_msgs = processor.dict_to_langchain(original_dict)
    final_dict = processor.langchain_to_dict(lc_msgs)

    assert len(final_dict) == len(original_dict)
    for orig, final in zip(original_dict, final_dict):
        assert orig["role"] == final["role"]
        assert orig["content"] == final["content"]


def test_chinese_content_handling():
    """测试中文内容处理"""
    processor = MessageProcessor()

    dict_msgs = [
        {"role": "user", "content": "你好，世界！这是一个测试。"},
        {"role": "assistant", "content": "你好！我理解中文。"}
    ]

    lc_msgs = processor.dict_to_langchain(dict_msgs)
    back_to_dict = processor.langchain_to_dict(lc_msgs)

    assert back_to_dict[0]["content"] == "你好，世界！这是一个测试。"
    assert back_to_dict[1]["content"] == "你好！我理解中文。"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
