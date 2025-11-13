"""
日志配置模块

提供统一的日志配置和管理功能。
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class RAGLogger:
    """
    RAG系统日志管理器
    
    提供统一的日志配置，支持多种日志级别、文件输出和控制台输出。
    
    示例:
        >>> from rag5.utils.logging_config import RAGLogger
        >>> 
        >>> # 配置日志系统
        >>> RAGLogger.setup_logging(
        ...     log_level="DEBUG",
        ...     log_file="logs/rag_debug.log",
        ...     enable_console=True
        ... )
        >>> 
        >>> # 获取日志记录器
        >>> logger = RAGLogger.get_logger(__name__)
        >>> logger.info("这是一条信息日志")
    """
    
    _initialized = False
    _log_file: Optional[str] = None
    _log_level: str = "INFO"
    
    @staticmethod
    def setup_logging(
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        enable_console: bool = True,
        log_format: Optional[str] = None
    ) -> None:
        """
        配置日志系统
        
        参数:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: 日志文件路径，如果为None则不输出到文件
            enable_console: 是否输出到控制台
            log_format: 自定义日志格式，如果为None则使用默认格式
        
        示例:
            >>> RAGLogger.setup_logging(
            ...     log_level="DEBUG",
            ...     log_file="logs/rag_app.log",
            ...     enable_console=True
            ... )
        """
        # 验证日志级别
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level.upper() not in valid_levels:
            raise ValueError(
                f"无效的日志级别: {log_level}. "
                f"有效值: {', '.join(valid_levels)}"
            )
        
        RAGLogger._log_level = log_level.upper()
        RAGLogger._log_file = log_file
        
        # 默认日志格式：[时间戳] [级别] [模块名] [函数名] - 消息
        if log_format is None:
            log_format = (
                "[%(asctime)s] [%(levelname)s] [%(name)s] "
                "[%(funcName)s] - %(message)s"
            )
        
        # 时间格式
        date_format = "%Y-%m-%d %H:%M:%S"
        
        # 创建格式化器
        formatter = logging.Formatter(log_format, datefmt=date_format)
        
        # 获取根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, RAGLogger._log_level))
        
        # 清除现有的处理器
        root_logger.handlers.clear()
        
        # 添加控制台处理器
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, RAGLogger._log_level))
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # 添加文件处理器
        if log_file:
            # 确保日志目录存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(
                log_file,
                mode='a',
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, RAGLogger._log_level))
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        RAGLogger._initialized = True
        
        # 记录初始化信息
        logger = RAGLogger.get_logger("RAGLogger")
        logger.info("=" * 60)
        logger.info("日志系统初始化完成")
        logger.info(f"日志级别: {RAGLogger._log_level}")
        logger.info(f"控制台输出: {'启用' if enable_console else '禁用'}")
        logger.info(f"文件输出: {log_file if log_file else '禁用'}")
        logger.info("=" * 60)
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器
        
        如果日志系统未初始化，将使用默认配置初始化。
        
        参数:
            name: 日志记录器名称（通常使用 __name__）
        
        返回:
            日志记录器实例
        
        示例:
            >>> logger = RAGLogger.get_logger(__name__)
            >>> logger.info("这是一条信息")
        """
        # 如果未初始化，使用默认配置
        if not RAGLogger._initialized:
            RAGLogger.setup_logging()
        
        return logging.getLogger(name)
    
    @staticmethod
    def set_level(log_level: str) -> None:
        """
        动态设置日志级别
        
        参数:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
        示例:
            >>> RAGLogger.set_level("DEBUG")
        """
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level.upper() not in valid_levels:
            raise ValueError(
                f"无效的日志级别: {log_level}. "
                f"有效值: {', '.join(valid_levels)}"
            )
        
        RAGLogger._log_level = log_level.upper()
        
        # 更新根日志记录器和所有处理器的级别
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, RAGLogger._log_level))
        
        for handler in root_logger.handlers:
            handler.setLevel(getattr(logging, RAGLogger._log_level))
        
        logger = RAGLogger.get_logger("RAGLogger")
        logger.info(f"日志级别已更新为: {RAGLogger._log_level}")
    
    @staticmethod
    def get_current_level() -> str:
        """
        获取当前日志级别
        
        返回:
            当前日志级别
        
        示例:
            >>> level = RAGLogger.get_current_level()
            >>> print(f"当前日志级别: {level}")
        """
        return RAGLogger._log_level
    
    @staticmethod
    def is_initialized() -> bool:
        """
        检查日志系统是否已初始化
        
        返回:
            是否已初始化
        
        示例:
            >>> if RAGLogger.is_initialized():
            ...     print("日志系统已初始化")
        """
        return RAGLogger._initialized
    
    @staticmethod
    def reset() -> None:
        """
        重置日志系统
        
        清除所有处理器和配置，用于测试或重新初始化。
        
        示例:
            >>> RAGLogger.reset()
            >>> RAGLogger.setup_logging(log_level="DEBUG")
        """
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        RAGLogger._initialized = False
        RAGLogger._log_file = None
        RAGLogger._log_level = "INFO"


def setup_default_logging() -> None:
    """
    使用默认配置设置日志系统
    
    默认配置:
    - 日志级别: INFO
    - 控制台输出: 启用
    - 文件输出: logs/rag_app.log
    
    示例:
        >>> from rag5.utils.logging_config import setup_default_logging
        >>> setup_default_logging()
    """
    RAGLogger.setup_logging(
        log_level="INFO",
        log_file="logs/rag_app.log",
        enable_console=True
    )
