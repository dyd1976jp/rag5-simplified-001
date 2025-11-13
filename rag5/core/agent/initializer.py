"""
代理初始化模块

负责代理的初始化和依赖检查，包括服务可用性检查、LLM 初始化和工具加载。
"""

import logging
import requests
from typing import Dict, List, Any, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

from rag5.config.settings import settings
from rag5.core.prompts import SYSTEM_PROMPT
from rag5.tools import get_tools
from rag5.utils.llm_logger import LLMCallLogger, ChatOllamaWithLogging
from rag5.utils.id_generator import generate_session_id

logger = logging.getLogger(__name__)


class AgentInitializer:
    """
    代理初始化器

    负责检查服务可用性、初始化 LLM 和工具，并创建代理执行器。

    示例:
        >>> from rag5.core.agent.initializer import AgentInitializer
        >>>
        >>> initializer = AgentInitializer()
        >>>
        >>> # 检查服务
        >>> status = initializer.check_services()
        >>> if all(status.values()):
        ...     # 创建代理
        ...     agent = initializer.create_agent()
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        初始化代理初始化器
        
        参数:
            session_id: 可选的会话 ID，用于日志跟踪。如果未提供，将自动生成。
        """
        self._llm = None
        self._llm_logger = None
        self._tools = None
        self._agent_executor = None
        self._session_id = session_id or generate_session_id("session")

    def check_ollama_service(self) -> bool:
        """
        检查 Ollama 服务是否可用

        返回:
            服务是否可用

        示例:
            >>> initializer = AgentInitializer()
            >>> if initializer.check_ollama_service():
            ...     print("Ollama 服务可用")
        """
        try:
            response = requests.get(
                f"{settings.ollama_host}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                logger.debug("✓ Ollama 服务可用")
                return True
            else:
                logger.warning(f"Ollama 服务返回状态码: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"无法连接到 Ollama 服务 ({settings.ollama_host}): {e}")
            return False

    def check_ollama_model(self, model_name: str) -> bool:
        """
        检查 Ollama 模型是否可用

        参数:
            model_name: 模型名称

        返回:
            模型是否可用

        示例:
            >>> initializer = AgentInitializer()
            >>> if initializer.check_ollama_model("qwen2.5:7b"):
            ...     print("模型可用")
        """
        try:
            response = requests.get(
                f"{settings.ollama_host}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [m.get("name", "") for m in models]

                # 检查模型是否在列表中
                is_available = any(model_name in m for m in available_models)

                if is_available:
                    logger.debug(f"✓ 模型 '{model_name}' 可用")
                else:
                    logger.warning(
                        f"模型 '{model_name}' 不可用. "
                        f"可用模型: {', '.join(available_models)}"
                    )

                return is_available
            else:
                logger.warning(f"无法获取模型列表，状态码: {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"检查模型可用性时出错: {e}")
            return False

    def check_services(self) -> Dict[str, bool]:
        """
        检查所有必需服务的可用性

        返回:
            服务状态字典，键为服务名称，值为是否可用

        示例:
            >>> initializer = AgentInitializer()
            >>> status = initializer.check_services()
            >>> print(f"Ollama 服务: {'✓' if status['ollama'] else '✗'}")
            >>> print(f"LLM 模型: {'✓' if status['llm_model'] else '✗'}")
            >>> print(f"嵌入模型: {'✓' if status['embed_model'] else '✗'}")
        """
        logger.info("检查服务可用性...")

        status = {
            "ollama": False,
            "llm_model": False,
            "embed_model": False
        }

        # 检查 Ollama 服务
        status["ollama"] = self.check_ollama_service()

        if status["ollama"]:
            # 检查 LLM 模型
            status["llm_model"] = self.check_ollama_model(settings.llm_model)

            # 检查嵌入模型
            status["embed_model"] = self.check_ollama_model(settings.embed_model)

        # 记录检查结果
        for service, available in status.items():
            if available:
                logger.info(f"✓ {service}: 可用")
            else:
                logger.error(f"✗ {service}: 不可用")

        return status

    def initialize_llm(self) -> ChatOllama:
        """
        初始化 LLM

        返回:
            ChatOllama 实例（如果启用日志记录，则为 ChatOllamaWithLogging）

        异常:
            ConnectionError: Ollama 服务不可用
            ValueError: LLM 模型不可用

        示例:
            >>> initializer = AgentInitializer()
            >>> llm = initializer.initialize_llm()
            >>> print(f"LLM 模型: {llm.model}")
        """
        logger.info("初始化 LLM...")

        # 检查 Ollama 服务
        if not self.check_ollama_service():
            error_msg = (
                f"无法连接到 Ollama 服务 ({settings.ollama_host}). "
                f"请确保 Ollama 正在运行: ollama serve"
            )
            logger.error(error_msg)
            raise ConnectionError(error_msg)

        # 检查 LLM 模型
        if not self.check_ollama_model(settings.llm_model):
            error_msg = (
                f"LLM 模型 '{settings.llm_model}' 不可用. "
                f"请运行: ollama pull {settings.llm_model}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 初始化 ChatOllama
        try:
            # Check if enhanced LLM logging is enabled
            if settings.enable_llm_logging:
                # Create LLM logger with redaction support and async writing
                self._llm_logger = LLMCallLogger(
                    log_file=settings.llm_log_file,
                    enable_prompt_logging=settings.log_prompts,
                    enable_response_logging=settings.log_responses,
                    redact_sensitive=settings.redact_sensitive,  # Backward compatibility
                    redact_prompts=settings.redact_prompts,
                    redact_responses=settings.redact_responses,
                    async_logging=settings.async_logging,
                    buffer_size=settings.log_buffer_size,
                    max_entry_size=settings.max_log_entry_size
                )
                
                # Create ChatOllama with logging
                self._llm = ChatOllamaWithLogging(
                    llm_logger=self._llm_logger,
                    session_id=self._session_id,
                    model=settings.llm_model,
                    base_url=settings.ollama_host,
                    temperature=0.1,  # 低温度以保持一致性
                    timeout=settings.llm_timeout
                )
                logger.info(f"✓ 初始化 LLM (带日志记录): {settings.llm_model}")
            else:
                # Create standard ChatOllama without logging
                self._llm = ChatOllama(
                    model=settings.llm_model,
                    base_url=settings.ollama_host,
                    temperature=0.1,  # 低温度以保持一致性
                    timeout=settings.llm_timeout
                )
                logger.info(f"✓ 初始化 LLM: {settings.llm_model}")
            
            return self._llm
        except Exception as e:
            logger.error(f"初始化 LLM 失败: {e}")
            raise

    def initialize_tools(self) -> List[Any]:
        """
        初始化工具

        返回:
            工具列表

        异常:
            Exception: 工具加载失败

        示例:
            >>> initializer = AgentInitializer()
            >>> tools = initializer.initialize_tools()
            >>> print(f"加载了 {len(tools)} 个工具")
        """
        logger.info("加载工具...")

        try:
            self._tools = get_tools()
            tool_names = [tool.name for tool in self._tools]
            logger.info(f"✓ 加载了 {len(self._tools)} 个工具: {', '.join(tool_names)}")
            return self._tools
        except Exception as e:
            logger.error(f"加载工具失败: {e}")
            raise

    def create_agent(self) -> Any:
        """
        创建代理执行器

        返回:
            代理执行器

        异常:
            ConnectionError: Ollama 服务不可用
            ValueError: 模型不可用
            Exception: 代理创建失败

        示例:
            >>> initializer = AgentInitializer()
            >>> agent = initializer.create_agent()
            >>> # 使用代理
            >>> result = agent.invoke({"messages": [...]})
        """
        logger.info("创建代理...")

        # 初始化 LLM（如果尚未初始化）
        if self._llm is None:
            self.initialize_llm()

        # 初始化工具（如果尚未初始化）
        if self._tools is None:
            self.initialize_tools()

        # 创建 React 代理
        try:
            self._agent_executor = create_react_agent(
                model=self._llm,
                tools=self._tools,
                prompt=SystemMessage(content=SYSTEM_PROMPT)
            )
            logger.info("✓ 代理创建成功")
            return self._agent_executor
        except Exception as e:
            logger.error(f"创建代理失败: {e}")
            raise

    @property
    def llm(self) -> ChatOllama:
        """
        获取 LLM 实例

        如果 LLM 未初始化，将自动初始化。

        返回:
            ChatOllama 实例
        """
        if self._llm is None:
            self.initialize_llm()
        return self._llm

    @property
    def tools(self) -> List[Any]:
        """
        获取工具列表

        如果工具未初始化，将自动初始化。

        返回:
            工具列表
        """
        if self._tools is None:
            self.initialize_tools()
        return self._tools

    @property
    def agent_executor(self) -> Any:
        """
        获取代理执行器

        如果代理未创建，将自动创建。

        返回:
            代理执行器
        """
        if self._agent_executor is None:
            self.create_agent()
        return self._agent_executor

    @property
    def session_id(self) -> str:
        """
        获取会话 ID

        返回:
            会话 ID 字符串
        """
        return self._session_id

    def shutdown(self, timeout: float = 5.0) -> None:
        """
        优雅地关闭初始化器并刷新所有日志缓冲区
        
        参数:
            timeout: 等待关闭的最大时间（秒）
        """
        if self._llm_logger:
            try:
                self._llm_logger.shutdown(timeout=timeout)
                logger.debug("✓ LLM 日志记录器已关闭")
            except Exception as e:
                logger.error(f"关闭 LLM 日志记录器时出错: {e}")
    
    def __repr__(self) -> str:
        """返回初始化器的字符串表示"""
        llm_status = "initialized" if self._llm else "not initialized"
        tools_status = f"{len(self._tools)} tools" if self._tools else "not initialized"
        agent_status = "created" if self._agent_executor else "not created"

        return (
            f"<AgentInitializer("
            f"session_id={self._session_id}, "
            f"llm={llm_status}, "
            f"tools={tools_status}, "
            f"agent={agent_status}"
            f")>"
        )
