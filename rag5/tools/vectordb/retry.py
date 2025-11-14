"""
重试逻辑模块

提供带指数退避的重试装饰器，用于处理临时性错误。
"""

import time
import logging
from typing import Callable, Any, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)

# 重试配置常量
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_DELAY = 1.0  # 秒
DEFAULT_MAX_DELAY = 10.0  # 秒
DEFAULT_BACKOFF_FACTOR = 2.0


def retry_with_backoff(
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = DEFAULT_INITIAL_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    带指数退避的重试装饰器

    当函数执行失败时，自动重试指定次数，每次重试之间的延迟呈指数增长。

    参数:
        max_retries: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        backoff_factor: 退避因子（每次重试延迟乘以此因子）
        exceptions: 需要重试的异常类型元组

    返回:
        装饰器函数

    示例:
        >>> @retry_with_backoff(max_retries=3, initial_delay=1.0)
        ... def unstable_function():
        ...     # 可能失败的操作
        ...     return api_call()
        >>>
        >>> result = unstable_function()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"函数 {func.__name__} 第 {attempt + 1}/{max_retries} 次尝试失败: {e}. "
                            f"将在 {delay:.1f}s 后重试..."
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        logger.error(f"函数 {func.__name__} 所有 {max_retries} 次尝试均失败")

            # 所有重试都失败，抛出最后一个异常
            raise last_exception

        return wrapper
    return decorator


def execute_with_retry(
    func: Callable,
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = DEFAULT_INITIAL_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
) -> Any:
    """
    执行函数并在失败时重试

    这是一个函数式的重试实现，不使用装饰器。

    参数:
        func: 要执行的函数
        max_retries: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        backoff_factor: 退避因子

    返回:
        函数执行结果

    异常:
        最后一次执行的异常

    示例:
        >>> result = execute_with_retry(
        ...     lambda: api_call(),
        ...     max_retries=3,
        ...     initial_delay=1.0
        ... )
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.warning(
                    f"第 {attempt + 1}/{max_retries} 次尝试失败: {e}. "
                    f"将在 {delay:.1f}s 后重试..."
                )
                time.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)
            else:
                logger.error(f"所有 {max_retries} 次尝试均失败")

    raise last_exception
