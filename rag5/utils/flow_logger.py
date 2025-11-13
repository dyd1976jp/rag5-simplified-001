"""
Flow logger for unified flow-based logging.

This module provides the main logging interface for unified flow logs that
capture all events in a query processing flow in chronological order.
"""

import logging
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

from rag5.utils.flow_formatter import FlowFormatter
from rag5.utils.async_writer import AsyncLogWriter, register_async_writer

logger = logging.getLogger(__name__)


class FlowLogger:
    """
    Logger for unified flow-based logging.
    
    Captures all events in a query processing flow and writes them
    to a single, chronologically ordered log file with human-readable formatting.
    
    This logger tracks the complete journey from user query to final answer,
    including query analysis, tool selection and execution, LLM calls, and errors.
    
    Attributes:
        log_file: Path to unified flow log file
        session_id: Unique identifier for this query session
        enabled: Whether flow logging is enabled
        detail_level: Level of detail ("minimal", "normal", "verbose")
        max_content_length: Maximum length for content before truncation
        async_logging: Whether to use async writing
        
    Example:
        >>> from rag5.utils.flow_logger import FlowLogger
        >>> 
        >>> # Create flow logger for a query session
        >>> logger = FlowLogger(
        ...     log_file="logs/unified_flow.log",
        ...     session_id="abc-123-def",
        ...     detail_level="normal"
        ... )
        >>> 
        >>> # Log query start
        >>> logger.log_query_start("What is the capital of France?")
        >>> 
        >>> # Log tool execution
        >>> logger.log_tool_execution(
        ...     tool_name="search",
        ...     tool_input="capital of France",
        ...     tool_output="Paris is the capital",
        ...     duration_seconds=0.5
        ... )
        >>> 
        >>> # Log query completion
        >>> logger.log_query_complete(
        ...     final_answer="The capital of France is Paris.",
        ...     total_duration_seconds=2.5
        ... )
    """
    
    def __init__(
        self,
        log_file: str,
        session_id: str,
        enabled: bool = True,
        detail_level: str = "normal",
        max_content_length: int = 500,
        async_logging: bool = True
    ):
        """
        Initialize flow logger.
        
        Args:
            log_file: Path to unified flow log file
            session_id: Unique identifier for this query session
            enabled: Whether flow logging is enabled
            detail_level: Level of detail ("minimal", "normal", "verbose")
            max_content_length: Maximum length for content before truncation
            async_logging: Whether to use async writing
        """
        self.log_file = log_file
        self.session_id = session_id
        self.enabled = enabled
        self.detail_level = detail_level
        self.max_content_length = max_content_length
        self.async_logging = async_logging
        
        # Track query start time for elapsed time calculation
        self._start_time: Optional[float] = None
        
        # Initialize formatter
        self.formatter = FlowFormatter(
            detail_level=detail_level,
            max_content_length=max_content_length
        )
        
        # Initialize async writer if enabled
        self._async_writer: Optional[AsyncLogWriter] = None
        if enabled and async_logging:
            try:
                # Ensure log directory exists
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Import settings to get rotation configuration
                from rag5.config import settings
                
                self._async_writer = AsyncLogWriter(
                    log_file=log_file,
                    buffer_size=100,
                    flush_interval=5.0,
                    enable_rotation=getattr(settings, 'flow_rotation_enabled', True),
                    rotation_type=getattr(settings, 'flow_rotation_type', 'size'),
                    max_bytes=getattr(settings, 'flow_max_bytes', 10 * 1024 * 1024),
                    rotation_when=getattr(settings, 'flow_rotation_when', 'midnight'),
                    backup_count=getattr(settings, 'flow_backup_count', 5),
                    compress_rotated=getattr(settings, 'flow_compress_rotated', True)
                )
                register_async_writer(self._async_writer)
                logger.debug(f"FlowLogger initialized with async writing for {log_file}")
            except Exception as e:
                logger.error(f"Failed to initialize async writer: {e}", exc_info=True)
                self._async_writer = None
        
        logger.debug(
            f"FlowLogger initialized (session={session_id}, enabled={enabled}, "
            f"detail_level={detail_level}, async={async_logging})"
        )
    
    def get_elapsed_time(self) -> float:
        """
        Get elapsed time since query start.
        
        Returns:
            Elapsed time in seconds, or 0.0 if query hasn't started
        """
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    def _write_log(self, log_entry: str) -> None:
        """
        Write a log entry to the file.
        
        Uses async writer if available, otherwise falls back to synchronous writing.
        Never raises exceptions - logs errors but continues execution.
        
        Args:
            log_entry: The formatted log entry to write
        """
        if not self.enabled:
            return
        
        try:
            if self._async_writer:
                # Use async writer for non-blocking writes
                self._async_writer.write(log_entry)
            else:
                # Fall back to synchronous writing
                log_path = Path(self.log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry + '\n')
        except Exception as e:
            # Never let logging failures break the application
            logger.warning(
                f"Failed to write flow log entry: {e}",
                exc_info=True
            )
    
    def log_query_start(
        self,
        query: str,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Log the start of a query processing session.
        
        This marks the beginning of a new query flow and resets the elapsed time tracker.
        
        Args:
            query: The user's query
            timestamp: Optional timestamp (defaults to now)
        """
        if not self.enabled:
            return
        
        try:
            # Reset start time for elapsed time tracking
            self._start_time = time.time()
            
            # Use provided timestamp or current time
            ts = timestamp or datetime.now()
            
            # Format and write log entry
            log_entry = self.formatter.format_query_start(
                session_id=self.session_id,
                query=query,
                timestamp=ts
            )
            self._write_log(log_entry)
            
        except Exception as e:
            logger.warning(f"Failed to log query start: {e}", exc_info=True)
    
    def log_query_analysis(
        self,
        detected_intent: str,
        requires_tools: bool,
        reasoning: str,
        confidence: float
    ) -> None:
        """
        Log query analysis and intent detection.
        
        Args:
            detected_intent: The detected intent type
            requires_tools: Whether tools are needed
            reasoning: Explanation of the analysis
            confidence: Confidence score (0-1)
        """
        if not self.enabled:
            return
        
        try:
            elapsed_time = self.get_elapsed_time()
            
            log_entry = self.formatter.format_query_analysis(
                detected_intent=detected_intent,
                requires_tools=requires_tools,
                reasoning=reasoning,
                confidence=confidence,
                elapsed_time=elapsed_time
            )
            self._write_log(log_entry)
            
        except Exception as e:
            logger.warning(f"Failed to log query analysis: {e}", exc_info=True)
    
    def log_tool_selection(
        self,
        tool_name: str,
        rationale: str,
        confidence: float
    ) -> None:
        """
        Log tool selection decision.
        
        Args:
            tool_name: Name of the selected tool
            rationale: Reason for selecting this tool
            confidence: Confidence in the selection (0-1)
        """
        if not self.enabled:
            return
        
        try:
            elapsed_time = self.get_elapsed_time()
            
            log_entry = self.formatter.format_tool_selection(
                tool_name=tool_name,
                rationale=rationale,
                confidence=confidence,
                elapsed_time=elapsed_time
            )
            self._write_log(log_entry)
            
        except Exception as e:
            logger.warning(f"Failed to log tool selection: {e}", exc_info=True)
    
    def log_tool_execution(
        self,
        tool_name: str,
        tool_input: str,
        tool_output: str,
        duration_seconds: float,
        status: str = "success"
    ) -> None:
        """
        Log tool execution.
        
        Args:
            tool_name: Name of the tool
            tool_input: Input provided to the tool
            tool_output: Output from the tool
            duration_seconds: Execution time
            status: Execution status ("success" or "error")
        """
        if not self.enabled:
            return
        
        try:
            elapsed_time = self.get_elapsed_time()
            
            log_entry = self.formatter.format_tool_execution(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                duration_seconds=duration_seconds,
                elapsed_time=elapsed_time,
                status=status
            )
            self._write_log(log_entry)
            
        except Exception as e:
            logger.warning(f"Failed to log tool execution: {e}", exc_info=True)
    
    def log_llm_call(
        self,
        model: str,
        prompt: str,
        response: str,
        duration_seconds: float,
        token_usage: Optional[Dict[str, int]] = None,
        status: str = "success"
    ) -> None:
        """
        Log LLM call.
        
        Args:
            model: Model name
            prompt: Prompt sent to LLM
            response: Response from LLM
            duration_seconds: Call duration
            token_usage: Token usage statistics
            status: Call status ("success" or "error")
        """
        if not self.enabled:
            return
        
        try:
            elapsed_time = self.get_elapsed_time()
            
            log_entry = self.formatter.format_llm_call(
                model=model,
                prompt=prompt,
                response=response,
                duration_seconds=duration_seconds,
                elapsed_time=elapsed_time,
                token_usage=token_usage,
                status=status
            )
            self._write_log(log_entry)
            
        except Exception as e:
            logger.warning(f"Failed to log LLM call: {e}", exc_info=True)
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None
    ) -> None:
        """
        Log an error event.
        
        Args:
            error_type: Type of error
            error_message: Error message
            stack_trace: Optional stack trace
        """
        if not self.enabled:
            return
        
        try:
            elapsed_time = self.get_elapsed_time()
            
            log_entry = self.formatter.format_error(
                error_type=error_type,
                error_message=error_message,
                stack_trace=stack_trace,
                elapsed_time=elapsed_time
            )
            self._write_log(log_entry)
            
        except Exception as e:
            logger.warning(f"Failed to log error: {e}", exc_info=True)
    
    def log_query_complete(
        self,
        final_answer: str,
        total_duration_seconds: float,
        status: str = "success"
    ) -> None:
        """
        Log query completion.
        
        This marks the end of a query flow and logs the final answer and total processing time.
        
        Args:
            final_answer: The final answer provided to user
            total_duration_seconds: Total processing time
            status: Final status ("success" or "error")
        """
        if not self.enabled:
            return
        
        try:
            log_entry = self.formatter.format_query_complete(
                session_id=self.session_id,
                final_answer=final_answer,
                total_duration_seconds=total_duration_seconds,
                status=status
            )
            self._write_log(log_entry)
            
        except Exception as e:
            logger.warning(f"Failed to log query complete: {e}", exc_info=True)
    
    def flush(self) -> None:
        """
        Force immediate flush of buffered log entries.
        
        Only applicable when async logging is enabled.
        """
        if self._async_writer:
            try:
                self._async_writer.flush()
            except Exception as e:
                logger.warning(f"Failed to flush flow logger: {e}", exc_info=True)
