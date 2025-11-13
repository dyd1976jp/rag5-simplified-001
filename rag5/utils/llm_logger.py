"""
LLM call logging utilities for enhanced observability.

This module provides logging capabilities for LLM interactions, including
request/response logging, timing measurement, and token usage tracking.
"""

import logging
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

from rag5.utils.structured_formatter import StructuredLogFormatter
from rag5.utils.id_generator import generate_request_id
from rag5.utils.redactor import SensitiveDataRedactor
from rag5.utils.async_writer import AsyncLogWriter, register_async_writer

logger = logging.getLogger(__name__)


class LLMCallLogger:
    """
    Logger for LLM requests and responses.
    
    Captures all LLM interactions with timing, token usage, and structured
    formatting for analysis and debugging.
    
    Attributes:
        log_file: Path to the log file
        enable_prompt_logging: Whether to log prompts
        enable_response_logging: Whether to log responses
        redact_sensitive: Whether to redact sensitive data
    
    Example:
        >>> from rag5.utils.llm_logger import LLMCallLogger
        >>> 
        >>> # Create logger without redaction
        >>> logger = LLMCallLogger(log_file="logs/llm_interactions.log")
        >>> 
        >>> # Create logger with redaction enabled
        >>> secure_logger = LLMCallLogger(
        ...     log_file="logs/llm_interactions.log",
        ...     redact_prompts=True,
        ...     redact_responses=True
        ... )
        >>> 
        >>> # Log a request
        >>> logger.log_request(
        ...     request_id="req-123",
        ...     session_id="session-456",
        ...     model="qwen2.5:7b",
        ...     prompt="What is the capital of France?",
        ...     config={"temperature": 0.1}
        ... )
        >>> 
        >>> # Log a response
        >>> logger.log_response(
        ...     request_id="req-123",
        ...     session_id="session-456",
        ...     response="The capital of France is Paris.",
        ...     duration_seconds=1.234,
        ...     token_usage={"prompt_tokens": 10, "completion_tokens": 8}
        ... )
    """
    
    def __init__(
        self,
        log_file: str = "logs/llm_interactions.log",
        enable_prompt_logging: bool = True,
        enable_response_logging: bool = True,
        redact_sensitive: bool = False,
        redact_prompts: bool = False,
        redact_responses: bool = False,
        async_logging: bool = True,
        buffer_size: int = 100,
        max_entry_size: Optional[int] = None
    ):
        """
        Initialize the LLM call logger.
        
        Args:
            log_file: Path to the log file
            enable_prompt_logging: Whether to log prompts
            enable_response_logging: Whether to log responses
            redact_sensitive: Whether to redact sensitive data (deprecated, use redact_prompts/redact_responses)
            redact_prompts: Whether to redact prompts
            redact_responses: Whether to redact responses
            async_logging: Whether to use async writing for performance
            buffer_size: Buffer size for async writing
            max_entry_size: Maximum size in bytes for a single log entry
        """
        self.log_file = log_file
        self.enable_prompt_logging = enable_prompt_logging
        self.enable_response_logging = enable_response_logging
        self.async_logging = async_logging
        self.max_entry_size = max_entry_size
        
        # Support both old and new redaction parameters
        # If redact_sensitive is True, apply to both prompts and responses
        if redact_sensitive:
            redact_prompts = True
            redact_responses = True
        
        self.redact_prompts = redact_prompts
        self.redact_responses = redact_responses
        
        self.formatter = StructuredLogFormatter(max_entry_size=max_entry_size)
        self.redactor = SensitiveDataRedactor(
            redact_prompts=redact_prompts,
            redact_responses=redact_responses
        )
        
        # Log warning when redaction is enabled
        if redact_prompts or redact_responses:
            redaction_types = []
            if redact_prompts:
                redaction_types.append("prompts")
            if redact_responses:
                redaction_types.append("responses")
            logger.warning(
                f"Sensitive data redaction enabled for: {', '.join(redaction_types)}. "
                "This will reduce observability for debugging."
            )
        
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize async writer if enabled
        self._async_writer: Optional[AsyncLogWriter] = None
        if async_logging:
            # Import settings to get rotation configuration
            from rag5.config import settings
            
            self._async_writer = AsyncLogWriter(
                log_file=log_file,
                buffer_size=buffer_size,
                flush_interval=5.0,
                enable_rotation=settings.enable_log_rotation,
                rotation_type=settings.log_rotation_type,
                max_bytes=settings.log_max_bytes,
                rotation_when=settings.log_rotation_when,
                backup_count=settings.log_backup_count,
                compress_rotated=settings.log_compress_rotated
            )
            register_async_writer(self._async_writer)
            logger.debug(f"Async logging enabled for {log_file}")
    
    def _write_log(self, log_entry: str) -> None:
        """
        Write a log entry to the log file.
        
        Args:
            log_entry: JSON-formatted log entry string
        """
        try:
            if self._async_writer:
                # Use async writer for non-blocking writes
                self._async_writer.write(log_entry)
            else:
                # Fall back to synchronous writing
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry + '\n')
        except Exception as e:
            # Never let logging failures break the application
            logger.error(f"Failed to write to LLM log file: {e}", exc_info=True)
    
    def flush(self) -> None:
        """
        Force immediate flush of buffered log entries.
        
        Only applicable when async logging is enabled.
        """
        if self._async_writer:
            self._async_writer.flush()
    
    def shutdown(self, timeout: float = 5.0) -> None:
        """
        Shutdown the logger gracefully.
        
        Flushes all buffered entries and stops the async writer thread.
        
        Args:
            timeout: Maximum time to wait for shutdown
        """
        if self._async_writer:
            self._async_writer.shutdown(timeout=timeout)
    
    def log_request(
        self,
        request_id: str,
        session_id: str,
        model: str,
        prompt: str,
        config: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log an LLM request.
        
        Args:
            request_id: Unique identifier for this request
            session_id: Session identifier for conversation tracking
            model: Name of the LLM model
            prompt: The prompt text sent to the LLM
            config: Configuration parameters (temperature, timeout, etc.)
            correlation_id: Optional correlation ID for linking operations
        """
        if not self.enable_prompt_logging:
            return
        
        try:
            # Apply redaction to prompts when redact_prompts=True
            logged_prompt = self.redactor.redact_if_needed(prompt, "llm_request")
            
            # Apply size limiting if configured
            original_size = len(logged_prompt.encode('utf-8'))
            logged_prompt = self.formatter.truncate_if_needed(logged_prompt)
            
            # Log warning if truncation occurred
            if self.max_entry_size and original_size > self.max_entry_size:
                logger.warning(
                    f"LLM request prompt truncated from {original_size} bytes "
                    f"to fit within {self.max_entry_size} byte limit"
                )
            
            # Format and write log entry
            log_entry = self.formatter.format_llm_request(
                request_id=request_id,
                session_id=session_id,
                model=model,
                prompt=logged_prompt,
                config=config,
                correlation_id=correlation_id
            )
            
            self._write_log(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log LLM request: {e}", exc_info=True)
    
    def log_response(
        self,
        request_id: str,
        session_id: str,
        response: str,
        duration_seconds: float,
        token_usage: Optional[Dict[str, int]] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log an LLM response.
        
        Args:
            request_id: Unique identifier matching the request
            session_id: Session identifier for conversation tracking
            response: The response text from the LLM
            duration_seconds: Time taken for the request in seconds
            token_usage: Optional token usage statistics
            correlation_id: Optional correlation ID for linking operations
        """
        if not self.enable_response_logging:
            return
        
        try:
            # Apply redaction to responses when redact_responses=True
            logged_response = self.redactor.redact_if_needed(response, "llm_response")
            
            # Apply size limiting if configured
            original_size = len(logged_response.encode('utf-8'))
            logged_response = self.formatter.truncate_if_needed(logged_response)
            
            # Log warning if truncation occurred
            if self.max_entry_size and original_size > self.max_entry_size:
                logger.warning(
                    f"LLM response truncated from {original_size} bytes "
                    f"to fit within {self.max_entry_size} byte limit"
                )
            
            # Format and write log entry
            log_entry = self.formatter.format_llm_response(
                request_id=request_id,
                session_id=session_id,
                response=logged_response,
                duration_seconds=duration_seconds,
                token_usage=token_usage,
                correlation_id=correlation_id,
                status="success"
            )
            
            self._write_log(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log LLM response: {e}", exc_info=True)
    
    def log_error(
        self,
        request_id: str,
        session_id: str,
        error: Exception,
        duration_seconds: float,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log an LLM error.
        
        Args:
            request_id: Unique identifier matching the request
            session_id: Session identifier for conversation tracking
            error: The exception that occurred
            duration_seconds: Time taken before error occurred
            correlation_id: Optional correlation ID for linking operations
        """
        try:
            # Format and write log entry
            log_entry = self.formatter.format_llm_error(
                request_id=request_id,
                session_id=session_id,
                error_message=str(error),
                error_type=type(error).__name__,
                duration_seconds=duration_seconds,
                correlation_id=correlation_id
            )
            
            self._write_log(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log LLM error: {e}", exc_info=True)


class ChatOllamaWithLogging(ChatOllama):
    """
    ChatOllama wrapper that adds comprehensive logging.
    
    This wrapper intercepts all LLM calls and logs requests, responses,
    timing information, and token usage for observability and debugging.
    
    Attributes:
        llm_logger: The LLMCallLogger instance for logging
        session_id: Session identifier for conversation tracking
    
    Example:
        >>> from rag5.utils.llm_logger import ChatOllamaWithLogging, LLMCallLogger
        >>> 
        >>> # Create logger
        >>> llm_logger = LLMCallLogger()
        >>> 
        >>> # Create LLM with logging
        >>> llm = ChatOllamaWithLogging(
        ...     llm_logger=llm_logger,
        ...     session_id="session-123",
        ...     model="qwen2.5:7b",
        ...     base_url="http://localhost:11434"
        ... )
        >>> 
        >>> # Use normally - logging happens automatically
        >>> from langchain_core.messages import HumanMessage
        >>> result = llm.invoke([HumanMessage(content="Hello!")])
    """
    
    def __init__(
        self,
        llm_logger: LLMCallLogger,
        session_id: str,
        *args,
        **kwargs
    ):
        """
        Initialize ChatOllama with logging capability.
        
        Args:
            llm_logger: The LLMCallLogger instance for logging
            session_id: Session identifier for conversation tracking
            *args: Positional arguments for ChatOllama
            **kwargs: Keyword arguments for ChatOllama
        """
        super().__init__(*args, **kwargs)
        # Use object.__setattr__ to bypass Pydantic validation for private attributes
        object.__setattr__(self, '_llm_logger', llm_logger)
        object.__setattr__(self, '_session_id', session_id)
    
    def _format_messages(self, messages: List[BaseMessage]) -> str:
        """
        Format messages list into a single prompt string.
        
        Args:
            messages: List of messages to format
        
        Returns:
            Formatted prompt string
        """
        formatted_parts = []
        for msg in messages:
            role = msg.__class__.__name__.replace("Message", "").lower()
            content = msg.content
            formatted_parts.append(f"[{role}]: {content}")
        
        return "\n".join(formatted_parts)
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any
    ) -> ChatResult:
        """
        Override _generate to add logging.
        
        Args:
            messages: List of messages to send to the LLM
            stop: Optional list of stop sequences
            run_manager: Optional callback manager
            **kwargs: Additional keyword arguments
        
        Returns:
            ChatResult from the LLM
        
        Raises:
            Exception: Any exception from the underlying LLM call
        """
        # Generate unique request ID
        request_id = generate_request_id()
        
        # Format prompt for logging
        prompt = self._format_messages(messages)
        
        # Prepare config for logging
        config = {
            "temperature": getattr(self, 'temperature', None),
            "timeout": getattr(self, 'timeout', None),
        }
        
        # Add any additional kwargs to config
        if kwargs:
            config.update(kwargs)
        
        # Log request
        self._llm_logger.log_request(
            request_id=request_id,
            session_id=self._session_id,
            model=self.model,
            prompt=prompt,
            config=config
        )
        
        # Execute LLM call with timing
        start_time = time.time()
        try:
            result = super()._generate(messages, stop, run_manager, **kwargs)
            duration = time.time() - start_time
            
            # Extract response text
            response_text = result.generations[0].text if result.generations else ""
            
            # Extract token usage if available
            token_usage = None
            if result.llm_output and "token_usage" in result.llm_output:
                token_usage = result.llm_output["token_usage"]
            
            # Log response
            self._llm_logger.log_response(
                request_id=request_id,
                session_id=self._session_id,
                response=response_text,
                duration_seconds=duration,
                token_usage=token_usage
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log error
            self._llm_logger.log_error(
                request_id=request_id,
                session_id=self._session_id,
                error=e,
                duration_seconds=duration
            )
            
            # Re-raise the exception
            raise
