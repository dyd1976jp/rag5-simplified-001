"""
测试API接口模块
"""

import pytest
from unittest.mock import Mock, patch

# 尝试导入TestClient
try:
    from starlette.testclient import TestClient
    TEST_CLIENT_AVAILABLE = True
except ImportError:
    TEST_CLIENT_AVAILABLE = False


@pytest.fixture
def client():
    """创建测试客户端"""
    if not TEST_CLIENT_AVAILABLE:
        pytest.skip("TestClient not available")

    from rag5.interfaces.api import create_app
    app = create_app()

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_agent():
    """Mock代理"""
    with patch('rag5.interfaces.api.handlers.SimpleRAGAgent') as mock_agent_class:
        mock_agent_instance = Mock()
        mock_agent_instance.chat.return_value = "测试回答"
        mock_agent_class.return_value = mock_agent_instance
        yield mock_agent_instance


def test_health_endpoint(client):
    """测试健康检查端点"""
    with patch('rag5.interfaces.api.routes.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data


def test_chat_endpoint_basic_query(client, mock_agent):
    """测试聊天端点基本查询"""
    response = client.post(
        "/chat",
        json={"query": "你好"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["answer"] == "测试回答"


def test_chat_endpoint_with_history(client, mock_agent):
    """测试聊天端点带历史"""
    response = client.post(
        "/chat",
        json={
            "query": "第一个项目的进度如何？",
            "history": [
                {"role": "user", "content": "公司有哪些项目？"},
                {"role": "assistant", "content": "有Alpha、Beta、Gamma三个项目"}
            ]
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data


def test_chat_endpoint_empty_query(client):
    """测试聊天端点空查询"""
    response = client.post(
        "/chat",
        json={"query": ""}
    )

    assert response.status_code == 422  # 验证错误


def test_chat_endpoint_missing_query(client):
    """测试聊天端点缺少查询"""
    response = client.post(
        "/chat",
        json={}
    )

    assert response.status_code == 422  # 验证错误


def test_chat_endpoint_query_too_long(client):
    """测试聊天端点查询过长"""
    long_query = "a" * 3000  # 超过MAX_QUERY_LENGTH

    response = client.post(
        "/chat",
        json={"query": long_query}
    )

    assert response.status_code == 422  # 验证错误


def test_chat_endpoint_invalid_history_role(client):
    """测试聊天端点无效历史角色"""
    response = client.post(
        "/chat",
        json={
            "query": "test",
            "history": [
                {"role": "invalid_role", "content": "test"}
            ]
        }
    )

    assert response.status_code == 422  # 验证错误


def test_chat_endpoint_connection_error(client):
    """测试聊天端点连接错误"""
    with patch('rag5.interfaces.api.handlers.SimpleRAGAgent') as mock_agent_class:
        mock_agent = Mock()
        mock_agent.chat.side_effect = ConnectionError("服务不可用")
        mock_agent_class.return_value = mock_agent

        response = client.post(
            "/chat",
            json={"query": "test"}
        )

        assert response.status_code == 503  # 服务不可用


def test_chat_endpoint_internal_error(client):
    """测试聊天端点内部错误"""
    with patch('rag5.interfaces.api.handlers.SimpleRAGAgent') as mock_agent_class:
        mock_agent = Mock()
        mock_agent.chat.side_effect = Exception("内部错误")
        mock_agent_class.return_value = mock_agent

        response = client.post(
            "/chat",
            json={"query": "test"}
        )

        assert response.status_code == 500  # 内部服务器错误


def test_chat_endpoint_timeout(client):
    """测试聊天端点超时"""
    with patch('rag5.interfaces.api.handlers.SimpleRAGAgent') as mock_agent_class:
        mock_agent = Mock()
        mock_agent.chat.side_effect = TimeoutError("请求超时")
        mock_agent_class.return_value = mock_agent

        response = client.post(
            "/chat",
            json={"query": "test"}
        )

        assert response.status_code == 504  # 网关超时


def test_chat_endpoint_history_too_long(client):
    """测试聊天端点历史过长"""
    long_history = [
        {"role": "user", "content": f"message {i}"}
        for i in range(60)  # 超过最大50条
    ]

    response = client.post(
        "/chat",
        json={
            "query": "test",
            "history": long_history
        }
    )

    assert response.status_code == 422  # 验证错误


def test_chat_response_model(client, mock_agent):
    """测试聊天响应模型"""
    response = client.post(
        "/chat",
        json={"query": "test"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert isinstance(data["answer"], str)


def test_health_endpoint_degraded(client):
    """测试健康检查端点降级状态"""
    with patch('rag5.interfaces.api.routes.requests.get') as mock_get:
        mock_get.side_effect = Exception("连接失败")

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data


def test_chat_endpoint_whitespace_query(client):
    """测试聊天端点空白查询"""
    response = client.post(
        "/chat",
        json={"query": "   "}
    )

    assert response.status_code == 400  # 错误请求


def test_message_model_validation():
    """测试Message模型验证"""
    from rag5.interfaces.api.models import Message

    # 有效消息
    msg = Message(role="user", content="test")
    assert msg.role == "user"
    assert msg.content == "test"

    # 无效角色
    with pytest.raises(Exception):
        Message(role="invalid", content="test")


def test_chat_request_model():
    """测试ChatRequest模型"""
    from rag5.interfaces.api.models import ChatRequest

    # 基本请求
    request = ChatRequest(query="test")
    assert request.query == "test"
    assert request.history == []

    # 带历史的请求
    from rag5.interfaces.api.models import Message
    history = [Message(role="user", content="previous")]
    request = ChatRequest(query="test", history=history)
    assert len(request.history) == 1


def test_chat_response_model_structure():
    """测试ChatResponse模型结构"""
    from rag5.interfaces.api.models import ChatResponse

    response = ChatResponse(answer="test answer")
    assert response.answer == "test answer"


def test_chat_handler_initialization():
    """测试ChatHandler初始化"""
    from rag5.interfaces.api.handlers import ChatHandler

    mock_agent = Mock()
    handler = ChatHandler(agent=mock_agent)

    assert handler is not None


def test_chat_handler_handle_chat():
    """测试ChatHandler处理聊天"""
    from rag5.interfaces.api.handlers import ChatHandler
    from rag5.interfaces.api.models import ChatRequest

    mock_agent = Mock()
    mock_agent.chat.return_value = "测试回答"

    handler = ChatHandler(agent=mock_agent)
    request = ChatRequest(query="测试问题")

    response = handler.handle_chat(request)

    assert response.answer == "测试回答"
    assert mock_agent.chat.called


def test_api_cors_headers(client):
    """测试API CORS头"""
    response = client.options("/chat")

    # 检查是否有CORS相关头（如果实现了）
    # 这取决于实际实现


def test_api_error_response_format(client):
    """测试API错误响应格式"""
    response = client.post(
        "/chat",
        json={"query": ""}
    )

    assert response.status_code == 422
    data = response.json()
    # 应该有错误详情
    assert "detail" in data


def test_chinese_query_handling(client, mock_agent):
    """测试中文查询处理"""
    mock_agent.chat.return_value = "这是中文回答"

    response = client.post(
        "/chat",
        json={"query": "这是中文问题"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "中文" in data["answer"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
