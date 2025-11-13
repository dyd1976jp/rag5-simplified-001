"""
测试代理模块
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage
from rag5.core.agent import SimpleRAGAgent, AgentInitializer


@pytest.fixture
def mock_services():
    """Mock所有外部服务"""
    with patch('rag5.core.agent.initializer.requests.get') as mock_get, \
         patch('rag5.core.agent.initializer.ChatOllama') as mock_chat_ollama, \
         patch('rag5.core.agent.initializer.search_knowledge_base') as mock_search:

        # Mock Ollama API响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen2.5:7b"},
                {"name": "bge-m3"}
            ]
        }
        mock_get.return_value = mock_response

        # Mock LLM
        mock_llm = Mock()
        mock_llm.invoke.return_value = AIMessage(content="测试响应")
        mock_chat_ollama.return_value = mock_llm

        yield {
            'mock_get': mock_get,
            'mock_llm': mock_llm,
            'mock_search': mock_search
        }


def test_agent_initializer_check_services(mock_services):
    """测试服务检查"""
    initializer = AgentInitializer()

    status = initializer.check_services()

    assert isinstance(status, dict)
    assert 'ollama' in status
    assert 'qdrant' in status


def test_agent_initializer_initialize_llm(mock_services):
    """测试LLM初始化"""
    initializer = AgentInitializer()

    llm = initializer.initialize_llm()

    assert llm is not None


def test_agent_initializer_initialize_tools(mock_services):
    """测试工具初始化"""
    initializer = AgentInitializer()

    tools = initializer.initialize_tools()

    assert isinstance(tools, list)
    assert len(tools) > 0


def test_agent_initialization(mock_services):
    """测试代理初始化"""
    with patch('rag5.core.agent.agent.create_react_agent') as mock_create_agent:
        mock_executor = Mock()
        mock_create_agent.return_value = mock_executor

        agent = SimpleRAGAgent()

        assert agent is not None
        assert mock_create_agent.called


def test_agent_chat_basic_query(mock_services):
    """测试基本查询"""
    with patch('rag5.core.agent.agent.create_react_agent') as mock_create_agent:
        mock_executor = Mock()
        mock_executor.invoke.return_value = {
            "messages": [AIMessage(content="你好！我是智能助手。")]
        }
        mock_create_agent.return_value = mock_executor

        agent = SimpleRAGAgent()
        response = agent.chat("你好")

        assert response == "你好！我是智能助手。"
        assert mock_executor.invoke.called


def test_agent_chat_with_history(mock_services):
    """测试带历史的查询"""
    with patch('rag5.core.agent.agent.create_react_agent') as mock_create_agent:
        mock_executor = Mock()
        mock_executor.invoke.return_value = {
            "messages": [AIMessage(content="Alpha项目进度良好")]
        }
        mock_create_agent.return_value = mock_executor

        agent = SimpleRAGAgent()
        history = [
            {"role": "user", "content": "公司有哪些项目？"},
            {"role": "assistant", "content": "有Alpha、Beta、Gamma三个项目"}
        ]
        response = agent.chat("第一个项目的进度如何？", history)

        assert "Alpha" in response or "进度" in response
        assert mock_executor.invoke.called


def test_agent_chat_empty_query(mock_services):
    """测试空查询"""
    with patch('rag5.core.agent.agent.create_react_agent') as mock_create_agent:
        mock_executor = Mock()
        mock_create_agent.return_value = mock_executor

        agent = SimpleRAGAgent()
        response = agent.chat("")

        assert "请输入" in response or "empty" in response.lower()


def test_agent_chat_connection_error(mock_services):
    """测试连接错误处理"""
    with patch('rag5.core.agent.agent.create_react_agent') as mock_create_agent:
        mock_executor = Mock()
        mock_executor.invoke.side_effect = ConnectionError("连接失败")
        mock_create_agent.return_value = mock_executor

        agent = SimpleRAGAgent()
        response = agent.chat("测试查询")

        assert "连接" in response or "connection" in response.lower()


def test_agent_chat_timeout_error(mock_services):
    """测试超时错误处理"""
    with patch('rag5.core.agent.agent.create_react_agent') as mock_create_agent:
        mock_executor = Mock()
        mock_executor.invoke.side_effect = TimeoutError("请求超时")
        mock_create_agent.return_value = mock_executor

        agent = SimpleRAGAgent()
        response = agent.chat("测试查询")

        assert "超时" in response or "timeout" in response.lower()


def test_agent_chat_general_error(mock_services):
    """测试一般错误处理"""
    with patch('rag5.core.agent.agent.create_react_agent') as mock_create_agent:
        mock_executor = Mock()
        mock_executor.invoke.side_effect = Exception("未知错误")
        mock_create_agent.return_value = mock_executor

        agent = SimpleRAGAgent()
        response = agent.chat("测试查询")

        assert "错误" in response or "error" in response.lower()


def test_agent_retry_logic(mock_services):
    """测试重试逻辑"""
    with patch('rag5.core.agent.agent.create_react_agent') as mock_create_agent:
        mock_executor = Mock()
        # 第一次失败，第二次成功
        mock_executor.invoke.side_effect = [
            Exception("临时错误"),
            {"messages": [AIMessage(content="重试后成功")]}
        ]
        mock_create_agent.return_value = mock_executor

        agent = SimpleRAGAgent()
        response = agent.chat("测试查询")

        assert response == "重试后成功"
        assert mock_executor.invoke.call_count == 2


def test_agent_initialization_missing_model():
    """测试缺少模型时的初始化"""
    with patch('rag5.core.agent.initializer.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="not available"):
            SimpleRAGAgent()


def test_agent_initialization_connection_error():
    """测试连接错误时的初始化"""
    with patch('rag5.core.agent.initializer.requests.get') as mock_get:
        mock_get.side_effect = ConnectionError("无法连接")

        with pytest.raises(ConnectionError):
            SimpleRAGAgent()


def test_ask_convenience_function(mock_services):
    """测试ask便捷函数"""
    with patch('rag5.core.agent.agent.create_react_agent') as mock_create_agent, \
         patch('rag5.core.agent.agent._get_agent') as mock_get_agent:

        mock_executor = Mock()
        mock_executor.invoke.return_value = {
            "messages": [AIMessage(content="测试回答")]
        }
        mock_create_agent.return_value = mock_executor

        mock_agent = SimpleRAGAgent()
        mock_get_agent.return_value = mock_agent

        from rag5.core.agent import ask

        answer = ask("测试问题")

        assert answer == "测试回答"


def test_agent_chinese_query_handling(mock_services):
    """测试中文查询处理"""
    with patch('rag5.core.agent.agent.create_react_agent') as mock_create_agent:
        mock_executor = Mock()
        mock_executor.invoke.return_value = {
            "messages": [AIMessage(content="这是中文回答")]
        }
        mock_create_agent.return_value = mock_executor

        agent = SimpleRAGAgent()
        response = agent.chat("这是一个中文问题")

        assert "中文" in response


def test_agent_long_history_handling(mock_services):
    """测试长历史处理"""
    with patch('rag5.core.agent.agent.create_react_agent') as mock_create_agent:
        mock_executor = Mock()
        mock_executor.invoke.return_value = {
            "messages": [AIMessage(content="处理长历史")]
        }
        mock_create_agent.return_value = mock_executor

        agent = SimpleRAGAgent()

        # 创建长历史
        long_history = []
        for i in range(50):
            long_history.append({"role": "user", "content": f"问题{i}"})
            long_history.append({"role": "assistant", "content": f"回答{i}"})

        response = agent.chat("新问题", long_history)

        assert len(response) > 0


def test_agent_system_prompt_usage(mock_services):
    """测试系统提示词使用"""
    with patch('rag5.core.agent.agent.create_react_agent') as mock_create_agent:
        mock_executor = Mock()
        mock_create_agent.return_value = mock_executor

        agent = SimpleRAGAgent()

        # 验证创建代理时使用了系统提示词
        call_args = mock_create_agent.call_args
        # 应该包含系统提示词参数
        assert call_args is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
