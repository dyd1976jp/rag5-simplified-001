"""
RAG 代理模块

实现 SimpleRAGAgent 类，协调 LLM 和工具交互，处理用户查询。
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from rag5.core.agent.initializer import AgentInitializer
from rag5.core.agent.messages import MessageProcessor
from rag5.core.agent.errors import ErrorHandler, TimeoutError
from rag5.core.prompts import SYSTEM_PROMPT
from rag5.config.settings import settings
from rag5.utils.reflection_logger import AgentReflectionLogger
from rag5.utils.context_logger import ConversationContextLogger
from rag5.utils.flow_logger import FlowLogger
from rag5.utils.id_generator import generate_correlation_id

logger = logging.getLogger(__name__)


class SimpleRAGAgent:
    """
    简单 RAG 代理

    使用 LLM 和工具来回答用户查询。代理可以：
    - 分析查询以确定是否需要使用工具
    - 在搜索知识库之前优化查询
    - 从检索到的信息中合成答案
    - 处理带有聊天历史的多轮对话

    示例:
        >>> from rag5.core.agent import SimpleRAGAgent
        >>>
        >>> # 创建代理
        >>> agent = SimpleRAGAgent()
        >>>
        >>> # 简单查询
        >>> answer = agent.chat("你好")
        >>> print(answer)
        >>>
        >>> # 带历史的查询
        >>> history = [
        ...     {"role": "user", "content": "公司有哪些项目？"},
        ...     {"role": "assistant", "content": "有Alpha、Beta、Gamma三个项目"}
        ... ]
        >>> answer = agent.chat("第一个项目的进度如何？", chat_history=history)
        >>> print(answer)
    """

    def __init__(self):
        """
        初始化 RAG 代理

        包括验证和错误处理，用于缺失的模型。

        异常:
            ConnectionError: Ollama 服务不可用
            ValueError: 模型不可用
        """
        logger.info("初始化 SimpleRAGAgent...")

        # 初始化组件
        self._initializer = AgentInitializer()
        self._error_handler = ErrorHandler()
        
        # 初始化反思日志记录器（如果启用）
        self._reflection_logger = None
        if settings.enable_reflection_logging:
            self._reflection_logger = AgentReflectionLogger(
                log_file=settings.reflection_log_file,
                session_id=self._initializer.session_id,
                async_logging=settings.async_logging,
                buffer_size=settings.log_buffer_size
            )
            logger.info("✓ Agent 反思日志记录已启用")
        
        # 初始化对话上下文日志记录器（如果启用）
        self._context_logger = None
        if settings.enable_context_logging:
            self._context_logger = ConversationContextLogger(
                log_file=settings.context_log_file,
                session_id=self._initializer.session_id,
                async_logging=settings.async_logging,
                buffer_size=settings.log_buffer_size
            )
            logger.info("✓ 对话上下文日志记录已启用")
        
        # 初始化统一流程日志记录器（如果启用）
        self._flow_logger = None
        if settings.enable_flow_logging:
            self._flow_logger = FlowLogger(
                log_file=settings.flow_log_file,
                session_id=self._initializer.session_id,
                enabled=True,
                detail_level=settings.flow_detail_level,
                max_content_length=settings.flow_max_content_length,
                async_logging=settings.flow_async_logging
            )
            logger.info("✓ 统一流程日志记录已启用")
        
        # 初始化消息处理器（传入上下文日志记录器）
        self._message_processor = MessageProcessor(
            context_logger=self._context_logger
        )

        # 创建代理执行器
        try:
            self._agent_executor = self._initializer.create_agent()
            logger.info("✓ SimpleRAGAgent 初始化成功")
        except Exception as e:
            logger.error(f"初始化 SimpleRAGAgent 失败: {e}")
            raise

    def chat(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        kb_id: Optional[str] = None
    ) -> str:
        """
        处理用户查询（可选聊天历史和知识库）

        包括超时处理和重试逻辑。

        参数:
            query: 用户问题或输入
            chat_history: 可选的先前消息列表，格式为:
                         [{"role": "user", "content": "..."},
                          {"role": "assistant", "content": "..."}]
            kb_id: 可选的知识库 ID，用于指定搜索的知识库

        返回:
            代理生成的答案

        示例:
            >>> agent = SimpleRAGAgent()
            >>> answer = agent.chat("李小勇和人合作入股了什么公司")
            >>> print(answer)
            >>> # 使用指定知识库
            >>> answer = agent.chat("李小勇和人合作入股了什么公司", kb_id="kb_123")
            >>> print(answer)
        """
        # 验证查询
        if not query or not query.strip():
            return "请输入有效的问题。"

        try:
            logger.info(f"处理查询: {query[:100]}...")
            
            # 记录查询开始（统一流程日志）
            if self._flow_logger:
                self._flow_logger.log_query_start(query)
            
            # 生成关联 ID 用于跟踪此查询的所有操作
            correlation_id = generate_correlation_id("query")

            # 准备当前时间用于上下文
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 准备消息
            messages = []

            # 添加带当前时间的系统消息
            from rag5.core.prompts import KNOWLEDGEBASE_TOOL_PROMPT
            
            # 如果提供了 kb_id，添加到工具提示中
            kb_instruction = ""
            if kb_id:
                kb_instruction = f"\n\n重要提示：当使用 search_knowledge_base 工具时，必须传入 kb_id 参数值为 '{kb_id}'。这将确保只在指定的知识库中搜索。"
            
            system_prompt = SYSTEM_PROMPT.format(
                knowledgebase_tool_prompt=KNOWLEDGEBASE_TOOL_PROMPT + kb_instruction,
                current_datetime=current_time,
                chat_history=""
            )
            messages.append(SystemMessage(content=system_prompt))

            # 添加聊天历史（如果提供）
            history_message_count = 0
            if chat_history:
                history_messages = self._message_processor.dict_to_langchain(
                    chat_history
                )
                messages.extend(history_messages)
                history_message_count = len(chat_history)

            # 添加当前查询
            messages.append(HumanMessage(content=query))
            
            # 记录上下文大小（如果启用上下文日志）
            if self._context_logger:
                # 计算总内容长度
                total_content_length = len(system_prompt) + len(query)
                if chat_history:
                    total_content_length += sum(
                        len(msg.get("content", "")) for msg in chat_history
                    )
                
                # 估计 token 数量（粗略估计：2 个字符 ≈ 1 个 token）
                estimated_tokens = total_content_length // 2
                
                # 记录当前查询消息的添加
                self._context_logger.log_message_added(
                    role="user",
                    content_length=len(query),
                    total_messages=len(messages),
                    total_tokens=estimated_tokens,
                    correlation_id=correlation_id
                )

            logger.debug(f"为代理准备了 {len(messages)} 条消息（包括 {history_message_count} 条历史消息）")
            
            # 简单的意图检测：检查查询是否可能需要工具
            requires_tools = self._analyze_query_intent(query)
            detected_intent = "factual_lookup" if requires_tools else "conversational"
            reasoning = self._get_intent_reasoning(query, requires_tools)
            
            # 记录查询分析（如果启用反思日志）
            if self._reflection_logger:
                self._reflection_logger.log_query_analysis(
                    original_query=query,
                    detected_intent=detected_intent,
                    requires_tools=requires_tools,
                    reasoning=reasoning,
                    confidence=0.8,
                    correlation_id=correlation_id
                )
            
            # 记录查询分析（统一流程日志）
            if self._flow_logger:
                self._flow_logger.log_query_analysis(
                    detected_intent=detected_intent,
                    requires_tools=requires_tools,
                    reasoning=reasoning,
                    confidence=0.8
                )

            # 使用超时处理调用代理执行器
            max_retries = 2
            last_error = None

            for attempt in range(max_retries):
                try:
                    # 记录工具使用决策（如果启用反思日志）
                    if self._reflection_logger and requires_tools:
                        self._reflection_logger.log_tool_decision(
                            tool_name="search_knowledge_base",
                            decision_rationale="查询需要从知识库检索事实信息",
                            confidence=0.85,
                            query_context=query[:100],
                            correlation_id=correlation_id
                        )
                    
                    # 记录工具选择（统一流程日志）
                    if self._flow_logger and requires_tools:
                        self._flow_logger.log_tool_selection(
                            tool_name="search_knowledge_base",
                            rationale="查询需要从知识库检索事实信息",
                            confidence=0.85
                        )
                    
                    # 记录代理执行开始时间（用于工具执行计时）
                    import time
                    agent_start_time = time.time()
                    
                    # 准备配置，包括 kb_id（如果提供）
                    config = {"recursion_limit": 10}
                    if kb_id:
                        config["configurable"] = {"kb_id": kb_id}
                    
                    result = self._agent_executor.invoke(
                        {"messages": messages},
                        config=config
                    )
                    
                    # 记录工具执行（统一流程日志）
                    # 从结果中提取工具调用信息
                    if self._flow_logger and "messages" in result:
                        self._log_tool_executions_from_result(
                            result,
                            agent_start_time
                        )
                    
                    # 记录 LLM 调用（统一流程日志）
                    if self._flow_logger:
                        agent_duration = time.time() - agent_start_time
                        self._log_llm_calls_from_result(
                            result,
                            messages,
                            agent_duration
                        )

                    # 提取答案
                    answer = self._message_processor.extract_ai_response(result)
                    
                    # 记录合成决策（如果启用反思日志）
                    if self._reflection_logger:
                        # 估计使用的来源数量（基于答案中是否提到检索到的信息）
                        sources_used = self._estimate_sources_used(result)
                        has_sufficient_info = len(answer) > 50  # 简单启发式
                        
                        self._reflection_logger.log_synthesis_decision(
                            sources_used=sources_used,
                            confidence=0.9 if has_sufficient_info else 0.6,
                            reasoning="基于检索到的文档合成答案" if sources_used > 0 else "基于 LLM 知识生成答案",
                            has_sufficient_info=has_sufficient_info,
                            correlation_id=correlation_id
                        )
                    
                    # 记录查询完成（统一流程日志）
                    if self._flow_logger:
                        self._flow_logger.log_query_complete(
                            final_answer=answer,
                            total_duration_seconds=self._flow_logger.get_elapsed_time(),
                            status="success"
                        )

                    logger.info(f"生成答案，长度: {len(answer)}")
                    return answer

                except TimeoutError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"请求超时，正在重试... "
                            f"(尝试 {attempt + 1}/{max_retries})"
                        )
                        continue
                    else:
                        logger.error("所有重试后请求超时")
                        return self._error_handler.handle_timeout_error(
                            e,
                            "LLM 请求"
                        )

                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"请求失败: {e}，正在重试... "
                            f"(尝试 {attempt + 1}/{max_retries})"
                        )
                        continue
                    else:
                        # 最后一次尝试失败，抛出异常
                        raise

            # 如果所有重试都失败（不应该到达这里）
            if last_error:
                raise last_error

            return "抱歉，我无法生成回答。"

        except ConnectionError as e:
            logger.error(f"连接错误: {e}")
            # 记录错误（统一流程日志）
            if self._flow_logger:
                import traceback
                self._flow_logger.log_error(
                    error_type="ConnectionError",
                    error_message=str(e),
                    stack_trace=traceback.format_exc()
                )
                self._flow_logger.log_query_complete(
                    final_answer="",
                    total_duration_seconds=self._flow_logger.get_elapsed_time(),
                    status="error"
                )
            return self._error_handler.handle_connection_error(e, "Ollama/Qdrant")

        except ValueError as e:
            logger.error(f"配置错误: {e}")
            # 记录错误（统一流程日志）
            if self._flow_logger:
                import traceback
                self._flow_logger.log_error(
                    error_type="ValueError",
                    error_message=str(e),
                    stack_trace=traceback.format_exc()
                )
                self._flow_logger.log_query_complete(
                    final_answer="",
                    total_duration_seconds=self._flow_logger.get_elapsed_time(),
                    status="error"
                )
            return self._error_handler.handle_validation_error(e, "配置")

        except Exception as e:
            logger.error(f"处理查询时出错: {e}", exc_info=True)
            # 记录错误（统一流程日志）
            if self._flow_logger:
                import traceback
                self._flow_logger.log_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    stack_trace=traceback.format_exc()
                )
                self._flow_logger.log_query_complete(
                    final_answer="",
                    total_duration_seconds=self._flow_logger.get_elapsed_time(),
                    status="error"
                )
            return self._error_handler.handle_general_error(e, "处理您的问题")

    @property
    def initializer(self) -> AgentInitializer:
        """获取代理初始化器"""
        return self._initializer

    @property
    def message_processor(self) -> MessageProcessor:
        """获取消息处理器"""
        return self._message_processor

    @property
    def error_handler(self) -> ErrorHandler:
        """获取错误处理器"""
        return self._error_handler
    
    @property
    def reflection_logger(self) -> Optional[AgentReflectionLogger]:
        """获取反思日志记录器"""
        return self._reflection_logger
    
    @property
    def context_logger(self) -> Optional[ConversationContextLogger]:
        """获取对话上下文日志记录器"""
        return self._context_logger
    
    @property
    def flow_logger(self) -> Optional[FlowLogger]:
        """获取统一流程日志记录器"""
        return self._flow_logger
    
    def _analyze_query_intent(self, query: str) -> bool:
        """
        分析查询意图，判断是否需要工具
        
        参数:
            query: 用户查询
        
        返回:
            是否需要使用工具
        """
        # 简单的启发式规则：
        # - 包含疑问词（谁、什么、哪里、何时、为什么、如何）
        # - 包含具体实体名称（中文人名、公司名等）
        # - 查询较长（可能需要详细信息）
        
        question_words = ["谁", "什么", "哪", "何时", "为什么", "如何", "怎么", "多少"]
        has_question_word = any(word in query for word in question_words)
        
        # 检查是否包含可能的实体（简单检测：包含中文姓名模式）
        has_potential_entity = any(char.isupper() or len(query) > 10 for char in query)
        
        # 简单的问候语检测
        greetings = ["你好", "您好", "嗨", "hi", "hello", "早上好", "晚上好"]
        is_greeting = any(greeting in query.lower() for greeting in greetings)
        
        if is_greeting:
            return False
        
        return has_question_word or has_potential_entity
    
    def _get_intent_reasoning(self, query: str, requires_tools: bool) -> str:
        """
        获取意图检测的推理说明
        
        参数:
            query: 用户查询
            requires_tools: 是否需要工具
        
        返回:
            推理说明
        """
        if requires_tools:
            if any(word in query for word in ["谁", "什么", "哪"]):
                return "查询包含疑问词，可能需要从知识库检索事实信息"
            else:
                return "查询内容表明需要具体信息，建议使用知识库搜索"
        else:
            return "查询是简单对话或问候，可以直接由 LLM 回答"
    
    def _estimate_sources_used(self, result: Dict) -> int:
        """
        估计使用的来源数量
        
        参数:
            result: 代理执行结果
        
        返回:
            估计的来源数量
        """
        # 检查结果中是否有工具调用的迹象
        if "messages" in result:
            messages = result["messages"]
            # 计算工具消息的数量
            tool_messages = [
                msg for msg in messages 
                if hasattr(msg, "type") and "tool" in str(msg.type).lower()
            ]
            return len(tool_messages)
        
        return 0
    
    def _log_tool_executions_from_result(
        self,
        result: Dict,
        start_time: float
    ) -> None:
        """
        从代理执行结果中提取并记录工具执行信息
        
        参数:
            result: 代理执行结果
            start_time: 代理执行开始时间
        """
        if not self._flow_logger:
            return
        
        try:
            import time
            messages = result.get("messages", [])
            
            # 查找工具调用和工具消息对
            for i, msg in enumerate(messages):
                # 检查是否是 AI 消息且包含工具调用
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_name = tool_call.get("name", "unknown_tool")
                        tool_input = str(tool_call.get("args", {}))
                        
                        # 查找对应的工具响应消息
                        tool_output = ""
                        tool_status = "success"
                        for j in range(i + 1, len(messages)):
                            next_msg = messages[j]
                            if hasattr(next_msg, "type") and "tool" in str(next_msg.type).lower():
                                if hasattr(next_msg, "content"):
                                    tool_output = str(next_msg.content)
                                # 检查是否有错误
                                if hasattr(next_msg, "status") and next_msg.status == "error":
                                    tool_status = "error"
                                break
                        
                        # 估计工具执行时间（使用总时间的一部分）
                        duration = time.time() - start_time
                        
                        # 记录工具执行
                        self._flow_logger.log_tool_execution(
                            tool_name=tool_name,
                            tool_input=tool_input,
                            tool_output=tool_output,
                            duration_seconds=duration,
                            status=tool_status
                        )
        except Exception as e:
            logger.warning(f"从结果中记录工具执行失败: {e}", exc_info=True)
    
    def _log_llm_calls_from_result(
        self,
        result: Dict,
        input_messages: List,
        duration: float
    ) -> None:
        """
        从代理执行结果中提取并记录 LLM 调用信息
        
        参数:
            result: 代理执行结果
            input_messages: 输入消息列表
            duration: 总执行时间
        """
        if not self._flow_logger:
            return
        
        try:
            messages = result.get("messages", [])
            
            # 构建提示词（从输入消息）
            prompt_parts = []
            for msg in input_messages:
                if hasattr(msg, "content"):
                    prompt_parts.append(str(msg.content))
            prompt = "\n".join(prompt_parts)
            
            # 提取最终的 AI 响应
            response = ""
            for msg in reversed(messages):
                if hasattr(msg, "type") and "ai" in str(msg.type).lower():
                    if hasattr(msg, "content"):
                        response = str(msg.content)
                    break
            
            # 估计 token 使用量（粗略估计：2 个字符 ≈ 1 个 token）
            prompt_tokens = len(prompt) // 2
            response_tokens = len(response) // 2
            token_usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": response_tokens,
                "total_tokens": prompt_tokens + response_tokens
            }
            
            # 记录 LLM 调用
            self._flow_logger.log_llm_call(
                model=settings.llm_model,
                prompt=prompt,
                response=response,
                duration_seconds=duration,
                token_usage=token_usage,
                status="success"
            )
        except Exception as e:
            logger.warning(f"从结果中记录 LLM 调用失败: {e}", exc_info=True)

    def shutdown(self, timeout: float = 5.0) -> None:
        """
        优雅地关闭代理并刷新所有日志缓冲区
        
        参数:
            timeout: 等待关闭的最大时间（秒）
        """
        logger.info("正在关闭 SimpleRAGAgent...")
        
        # 关闭初始化器（包括 LLM 日志记录器）
        try:
            self._initializer.shutdown(timeout=timeout)
        except Exception as e:
            logger.error(f"关闭初始化器时出错: {e}")
        
        # 刷新反思日志记录器
        if self._reflection_logger:
            try:
                self._reflection_logger.shutdown(timeout=timeout)
                logger.debug("✓ 反思日志记录器已关闭")
            except Exception as e:
                logger.error(f"关闭反思日志记录器时出错: {e}")
        
        # 刷新上下文日志记录器
        if self._context_logger:
            try:
                self._context_logger.shutdown(timeout=timeout)
                logger.debug("✓ 上下文日志记录器已关闭")
            except Exception as e:
                logger.error(f"关闭上下文日志记录器时出错: {e}")
        
        # 刷新流程日志记录器
        if self._flow_logger:
            try:
                self._flow_logger.flush()
                logger.debug("✓ 流程日志记录器已关闭")
            except Exception as e:
                logger.error(f"关闭流程日志记录器时出错: {e}")
        
        logger.info("✓ SimpleRAGAgent 已关闭")
    
    def __repr__(self) -> str:
        """返回代理的字符串表示"""
        return f"<SimpleRAGAgent(initialized=True)>"


# 全局代理实例（延迟初始化）
_agent: Optional[SimpleRAGAgent] = None


def _get_agent() -> SimpleRAGAgent:
    """
    获取或创建全局代理实例（延迟初始化）

    返回:
        全局 SimpleRAGAgent 实例
    """
    global _agent
    if _agent is None:
        _agent = SimpleRAGAgent()
    return _agent


def ask(question: str, history: Optional[List[Dict[str, str]]] = None, kb_id: Optional[str] = None) -> str:
    """
    向代理提问的便捷函数

    此函数提供了一个简单的接口来使用代理，无需直接实例化 SimpleRAGAgent 类。

    参数:
        question: 用户问题
        history: 可选的聊天历史，格式为:
                [{"role": "user", "content": "..."},
                 {"role": "assistant", "content": "..."}]
        kb_id: 可选的知识库 ID，用于指定搜索的知识库

    返回:
        生成的答案

    示例:
        >>> from rag5.core.agent import ask
        >>>
        >>> answer = ask("李小勇和人合作入股了什么公司")
        >>> print(answer)
        >>>
        >>> # 带历史
        >>> history = [
        ...     {"role": "user", "content": "公司有哪些项目？"},
        ...     {"role": "assistant", "content": "有Alpha、Beta、Gamma三个项目"}
        ... ]
        >>> answer = ask("第一个项目的进度如何？", history)
        >>> print(answer)
        >>>
        >>> # 使用指定知识库
        >>> answer = ask("李小勇和人合作入股了什么公司", kb_id="kb_123")
        >>> print(answer)
    """
    agent = _get_agent()
    return agent.chat(question, history, kb_id=kb_id)


if __name__ == "__main__":
    # 测试代理
    logger.info("测试 SimpleRAGAgent...")

    # 测试基本查询
    print("\n" + "="*50)
    print("测试 1: 基本查询")
    print("="*50)
    test_query = "你好"
    answer = ask(test_query)
    print(f"\n查询: {test_query}")
    print(f"答案: {answer}")

    # 测试需要使用工具的查询
    print("\n" + "="*50)
    print("测试 2: 需要知识库搜索的查询")
    print("="*50)
    test_query = "李小勇和人合作入股了什么公司"
    answer = ask(test_query)
    print(f"\n查询: {test_query}")
    print(f"答案: {answer}")

    # 测试带聊天历史
    print("\n" + "="*50)
    print("测试 3: 多轮对话")
    print("="*50)
    history = [
        {"role": "user", "content": "公司有哪些项目？"},
        {"role": "assistant", "content": "有Alpha、Beta、Gamma三个项目"}
    ]
    test_query = "第一个项目的进度如何？"
    answer = ask(test_query, history)
    print(f"\n历史: {history}")
    print(f"查询: {test_query}")
    print(f"答案: {answer}")
