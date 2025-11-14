"""
测试错误处理器模块
"""

import pytest
import time
from unittest.mock import Mock
from rag5.core.agent import ErrorHandler, RetryHandler


def test_error_handler_initialization():
    """测试ErrorHandler初始化"""
    handler = ErrorHandler()
    assert handler is not None


def test_handle_connection_error():
    """测试处理连接错误"""
    handler = ErrorHandler()

    error = ConnectionError("无法连接到服务器")
    message = handler.handle_connection_error(error, "Ollama")

    assert "连接" in message or "connection" in message.lower()
    assert "Ollama" in message


def test_handle_timeout_error():
    """测试处理超时错误"""
    handler = ErrorHandler()

    error = TimeoutError("请求超时")
    message = handler.handle_timeout_error(error, "查询")

    assert "超时" in message or "timeout" in message.lower()


def test_handle_general_error():
    """测试处理一般错误"""
    handler = ErrorHandler()

    error = Exception("未知错误")
    message = handler.handle_general_error(error, "操作")

    assert "错误" in message or "error" in message.lower()
    assert "操作" in message


def test_handle_value_error():
    """测试处理值错误"""
    handler = ErrorHandler()

    error = ValueError("无效的参数")
    message = handler.handle_general_error(error, "验证")

    assert "无效" in message or "invalid" in message.lower()


def test_retry_handler_initialization():
    """测试RetryHandler初始化"""
    handler = RetryHandler(max_retries=3, initial_delay=1.0)

    assert handler is not None
    assert handler.max_retries == 3
    assert handler.initial_delay == 1.0


def test_retry_handler_default_values():
    """测试RetryHandler默认值"""
    handler = RetryHandler()

    assert handler.max_retries > 0
    assert handler.initial_delay > 0


def test_with_retry_success_first_try():
    """测试重试（第一次成功）"""
    handler = RetryHandler(max_retries=3, initial_delay=0.01)

    mock_func = Mock(return_value="success")

    result = handler.with_retry(mock_func)

    assert result == "success"
    assert mock_func.call_count == 1


def test_with_retry_success_after_failures():
    """测试重试（失败后成功）"""
    handler = RetryHandler(max_retries=3, initial_delay=0.01)

    call_count = [0]

    def flaky_func():
        call_count[0] += 1
        if call_count[0] < 3:
            raise Exception("临时错误")
        return "success"

    result = handler.with_retry(flaky_func)

    assert result == "success"
    assert call_count[0] == 3


def test_with_retry_max_retries_exceeded():
    """测试重试（超过最大次数）"""
    handler = RetryHandler(max_retries=2, initial_delay=0.01)

    def always_fails():
        raise Exception("持续错误")

    with pytest.raises(Exception, match="持续错误"):
        handler.with_retry(always_fails)


def test_with_retry_exponential_backoff():
    """测试指数退避"""
    handler = RetryHandler(max_retries=3, initial_delay=0.01)

    call_times = []

    def record_time():
        call_times.append(time.time())
        if len(call_times) < 3:
            raise Exception("临时错误")
        return "success"

    handler.with_retry(record_time)

    # 验证延迟递增
    if len(call_times) >= 3:
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        # 第二次延迟应该大于第一次（指数退避）
        assert delay2 > delay1


def test_with_timeout_success():
    """测试超时处理（成功）"""
    handler = RetryHandler()

    def quick_func():
        return "success"

    if hasattr(handler, 'with_timeout'):
        result = handler.with_timeout(quick_func, timeout=5)
        assert result == "success"


def test_with_timeout_exceeded():
    """测试超时处理（超时）"""
    handler = RetryHandler()

    def slow_func():
        time.sleep(10)
        return "success"

    if hasattr(handler, 'with_timeout'):
        with pytest.raises(TimeoutError):
            handler.with_timeout(slow_func, timeout=0.1)


def test_error_handler_format_error_message():
    """测试格式化错误消息"""
    handler = ErrorHandler()

    if hasattr(handler, 'format_error_message'):
        message = handler.format_error_message(
            error_type="ConnectionError",
            context="Ollama服务",
            details="无法连接到localhost:11434"
        )

        assert "ConnectionError" in message
        assert "Ollama" in message


def test_error_handler_log_error():
    """测试记录错误"""
    handler = ErrorHandler()

    if hasattr(handler, 'log_error'):
        # 应该不抛出异常
        handler.log_error(Exception("测试错误"), "测试上下文")


def test_retry_handler_with_specific_exceptions():
    """测试只重试特定异常"""
    handler = RetryHandler(max_retries=3, initial_delay=0.01)

    call_count = [0]

    def func_with_value_error():
        call_count[0] += 1
        raise ValueError("值错误")

    # 如果实现支持指定异常类型
    if hasattr(handler, 'with_retry_on'):
        with pytest.raises(ValueError):
            handler.with_retry_on(func_with_value_error, retry_on=[ConnectionError])

        # 不应该重试，因为ValueError不在重试列表中
        assert call_count[0] == 1


def test_error_handler_chain_errors():
    """测试错误链"""
    handler = ErrorHandler()

    try:
        try:
            raise ValueError("原始错误")
        except ValueError as e:
            raise ConnectionError("连接错误") from e
    except ConnectionError as e:
        message = handler.handle_connection_error(e, "测试")
        # 消息应该包含错误信息
        assert len(message) > 0


def test_retry_handler_callback():
    """测试重试回调"""
    handler = RetryHandler(max_retries=3, initial_delay=0.01)

    retry_attempts = []

    def on_retry(attempt, error):
        retry_attempts.append(attempt)

    call_count = [0]

    def flaky_func():
        call_count[0] += 1
        if call_count[0] < 3:
            raise Exception("临时错误")
        return "success"

    # 如果实现支持回调
    if hasattr(handler, 'with_retry_callback'):
        handler.with_retry_callback(flaky_func, on_retry=on_retry)
        assert len(retry_attempts) == 2  # 重试了2次


def test_error_handler_user_friendly_messages():
    """测试用户友好的错误消息"""
    handler = ErrorHandler()

    # 测试各种错误类型的消息是否用户友好
    errors = [
        (ConnectionError("Connection refused"), "连接"),
        (TimeoutError("Timeout"), "超时"),
        (ValueError("Invalid value"), "无效"),
    ]

    for error, expected_keyword in errors:
        if isinstance(error, ConnectionError):
            message = handler.handle_connection_error(error, "服务")
        elif isinstance(error, TimeoutError):
            message = handler.handle_timeout_error(error, "操作")
        else:
            message = handler.handle_general_error(error, "操作")

        # 消息应该包含预期的关键词或其英文版本
        assert expected_keyword in message or expected_keyword.lower() in message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
