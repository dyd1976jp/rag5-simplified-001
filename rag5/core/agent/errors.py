"""
错误处理模块

提供统一的错误处理和重试逻辑。
"""

import time
import logging
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """超时异常"""
    pass


class RetryHandler:
    """
    重试处理器

    提供带有指数退避的重试逻辑。
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0
    ):
        """
        初始化重试处理器

        Args:
            max_retries: 最大重试次数
            initial_delay: 初始延迟时间（秒）
            backoff_factor: 退避因子，每次重试延迟时间乘以此因子
            max_delay: 最大延迟时间（秒）
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay

    def with_retry(
        self,
        func: Callable,
        *args,
        exception_types: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs
    ) -> Any:
        """
        执行函数并在失败时重试

        Args:
            func: 要执行的函数
            *args: 函数的位置参数
            exception_types: 需要重试的异常类型元组
            **kwargs: 函数的关键字参数

        Returns:
            函数执行结果

        Raises:
            最后一次尝试的异常

        Example:
            >>> handler = RetryHandler(max_retries=3)
            >>> def unstable_function():
            ...     # 可能失败的函数
            ...     return "success"
            >>> result = handler.with_retry(unstable_function)
        """
        delay = self.initial_delay
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                last_exception = e

                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"尝试 {attempt + 1}/{self.max_retries} 失败: {str(e)}. "
                        f"将在 {delay:.1f} 秒后重试..."
                    )
                    time.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_delay)
                else:
                    logger.error(f"所有 {self.max_retries} 次尝试均失败")

        # 如果所有重试都失败，抛出最后一个异常
        raise last_exception

    def retry_decorator(
        self,
        exception_types: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """
        重试装饰器

        Args:
            exception_types: 需要重试的异常类型元组

        Returns:
            装饰器函数

        Example:
            >>> handler = RetryHandler(max_retries=3)
            >>> @handler.retry_decorator(exception_types=(ConnectionError,))
            ... def connect_to_service():
            ...     # 连接服务的代码
            ...     pass
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.with_retry(
                    func,
                    *args,
                    exception_types=exception_types,
                    **kwargs
                )
            return wrapper
        return decorator


class ErrorHandler:
    """
    统一错误处理器

    提供各种错误类型的统一处理方法。
    """

    @staticmethod
    def handle_connection_error(error: Exception, service_name: str = "服务") -> str:
        """
        处理连接错误

        Args:
            error: 异常对象
            service_name: 服务名称

        Returns:
            用户友好的错误消息

        Example:
            >>> handler = ErrorHandler()
            >>> message = handler.handle_connection_error(
            ...     ConnectionError("Connection refused"),
            ...     "Ollama"
            ... )
            >>> print(message)
            连接错误：无法连接到 Ollama 服务...
        """
        logger.error(f"连接 {service_name} 时出错: {error}")
        return f"连接错误：无法连接到 {service_name} 服务。请确保服务正在运行。"

    @staticmethod
    def handle_timeout_error(error: Exception, operation: str = "操作") -> str:
        """
        处理超时错误

        Args:
            error: 异常对象
            operation: 操作描述

        Returns:
            用户友好的错误消息

        Example:
            >>> handler = ErrorHandler()
            >>> message = handler.handle_timeout_error(
            ...     TimeoutError("Request timeout"),
            ...     "LLM 请求"
            ... )
            >>> print(message)
            超时错误：LLM 请求 超时...
        """
        logger.error(f"{operation} 超时: {error}")
        return f"超时错误：{operation} 超时。请稍后再试。"

    @staticmethod
    def handle_validation_error(error: Exception, field: str = "输入") -> str:
        """
        处理验证错误

        Args:
            error: 异常对象
            field: 字段名称

        Returns:
            用户友好的错误消息

        Example:
            >>> handler = ErrorHandler()
            >>> message = handler.handle_validation_error(
            ...     ValueError("Invalid value"),
            ...     "查询"
            ... )
            >>> print(message)
            验证错误：查询 无效...
        """
        logger.error(f"{field} 验证失败: {error}")
        return f"验证错误：{field} 无效。请检查输入。"

    @staticmethod
    def handle_model_error(error: Exception, model_name: str = "模型") -> str:
        """
        处理模型相关错误

        Args:
            error: 异常对象
            model_name: 模型名称

        Returns:
            用户友好的错误消息

        Example:
            >>> handler = ErrorHandler()
            >>> message = handler.handle_model_error(
            ...     ValueError("Model not found"),
            ...     "qwen2.5:7b"
            ... )
            >>> print(message)
            模型错误：模型 qwen2.5:7b 不可用...
        """
        logger.error(f"模型 {model_name} 错误: {error}")
        return f"模型错误：模型 {model_name} 不可用。请确保模型已安装。"

    @staticmethod
    def handle_general_error(error: Exception, context: str = "处理请求") -> str:
        """
        处理一般错误

        Args:
            error: 异常对象
            context: 错误上下文描述

        Returns:
            用户友好的错误消息

        Example:
            >>> handler = ErrorHandler()
            >>> message = handler.handle_general_error(
            ...     Exception("Unknown error"),
            ...     "查询处理"
            ... )
            >>> print(message)
            错误：查询处理 时出现问题...
        """
        logger.error(f"{context} 时出错: {error}", exc_info=True)
        return f"错误：{context} 时出现问题。错误信息：{str(error)}"

    @staticmethod
    def handle_error(
        error: Exception,
        error_type: Optional[str] = None,
        context: str = "操作"
    ) -> str:
        """
        统一错误处理入口

        根据错误类型自动选择合适的处理方法。

        Args:
            error: 异常对象
            error_type: 错误类型提示（可选）
            context: 错误上下文

        Returns:
            用户友好的错误消息

        Example:
            >>> handler = ErrorHandler()
            >>> try:
            ...     # 某些操作
            ...     raise ConnectionError("Connection failed")
            ... except Exception as e:
            ...     message = handler.handle_error(e, context="连接服务")
            ...     print(message)
        """
        # 根据异常类型自动选择处理方法
        if isinstance(error, ConnectionError) or "connection" in str(error).lower():
            return ErrorHandler.handle_connection_error(error, context)
        elif isinstance(error, TimeoutError) or "timeout" in str(error).lower():
            return ErrorHandler.handle_timeout_error(error, context)
        elif isinstance(error, ValueError) or "validation" in str(error).lower():
            return ErrorHandler.handle_validation_error(error, context)
        elif "model" in str(error).lower():
            return ErrorHandler.handle_model_error(error, context)
        else:
            return ErrorHandler.handle_general_error(error, context)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exception_types: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    带指数退避的重试装饰器（便捷函数）

    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        backoff_factor: 退避因子
        exception_types: 需要重试的异常类型元组

    Returns:
        装饰器函数

    Example:
        >>> @retry_with_backoff(max_retries=3, exception_types=(ConnectionError,))
        ... def connect_to_database():
        ...     # 连接数据库的代码
        ...     pass
    """
    handler = RetryHandler(
        max_retries=max_retries,
        initial_delay=initial_delay,
        backoff_factor=backoff_factor
    )
    return handler.retry_decorator(exception_types=exception_types)
