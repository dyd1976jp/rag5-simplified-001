"""
Structured log formatter for enhanced LLM logging.

This module provides JSON-based structured logging for LLM interactions,
agent reflections, and conversation context tracking.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredLogFormatter:
    """
    Formats logs as structured JSON with consistent schema.
    
    Provides methods for formatting different types of log entries:
    - LLM requests and responses
    - Agent reflections and reasoning
    - Conversation context changes
    
    All log entries include:
    - log_type: Type of log entry
    - timestamp: ISO 8601 timestamp with millisecond precision
    - request_id: Unique identifier for correlating requests/responses
    - session_id: Identifier for tracking conversation sessions
    - correlation_id: Identifier for linking related operations
    """
    
    def __init__(self, max_entry_size: Optional[int] = None):
        """
        Initialize the structured log formatter.
        
        Args:
            max_entry_size: Maximum size in bytes for a single log entry.
                           If None, no size limit is applied.
        """
        self.max_entry_size = max_entry_size
    
    @staticmethod
    def _get_timestamp() -> str:
        """
        Get current timestamp in ISO 8601 format with millisecond precision.
        
        Returns:
            Timestamp string (e.g., "2025-11-09T21:04:01.123Z")
        """
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    def truncate_if_needed(self, text: str, preserve_chars: int = 200) -> str:
        """
        Truncate text if it exceeds the maximum entry size.
        
        Preserves the first and last N characters for context and adds
        a truncation indicator showing the original size.
        
        Args:
            text: The text to potentially truncate
            preserve_chars: Number of characters to preserve from start and end
        
        Returns:
            Original text if within limits, or truncated text with indicator
        """
        if not self.max_entry_size:
            return text
        
        # Calculate size in bytes (UTF-8 encoding)
        text_bytes = len(text.encode('utf-8'))
        
        if text_bytes <= self.max_entry_size:
            return text
        
        # Calculate how many characters we can keep
        # We need space for the truncation indicator
        original_size = text_bytes
        truncation_msg = f"[TRUNCATED: original size {original_size} bytes]"
        
        # Preserve first and last N characters
        if len(text) <= preserve_chars * 2:
            # Text is too short to meaningfully truncate with context
            # Just truncate from the end
            max_chars = self.max_entry_size // 4  # Conservative estimate for UTF-8
            return text[:max_chars] + f"\n{truncation_msg}"
        
        # Keep first and last preserve_chars characters
        first_part = text[:preserve_chars]
        last_part = text[-preserve_chars:]
        
        truncated = f"{first_part}\n{truncation_msg}\n{last_part}"
        
        return truncated
    
    def format_llm_request(
        self,
        request_id: str,
        session_id: str,
        model: str,
        prompt: str,
        config: Dict[str, Any],
        correlation_id: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Format an LLM request as structured JSON.
        
        Args:
            request_id: Unique identifier for this request
            session_id: Session identifier for conversation tracking
            model: Name of the LLM model
            prompt: The prompt text sent to the LLM
            config: Configuration parameters (temperature, max_tokens, etc.)
            correlation_id: Optional correlation ID for linking operations
            timestamp: Optional timestamp (uses current time if not provided)
        
        Returns:
            JSON string representing the log entry
        """
        log_entry = {
            "log_type": "llm_request",
            "timestamp": timestamp or self._get_timestamp(),
            "request_id": request_id,
            "session_id": session_id,
            "correlation_id": correlation_id or request_id,
            "model": model,
            "prompt": prompt,
            "prompt_length": len(prompt),
            "config": config
        }
        
        return json.dumps(log_entry, ensure_ascii=False)
    
    def format_llm_response(
        self,
        request_id: str,
        session_id: str,
        response: str,
        duration_seconds: float,
        token_usage: Optional[Dict[str, int]] = None,
        correlation_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        status: str = "success"
    ) -> str:
        """
        Format an LLM response as structured JSON.
        
        Args:
            request_id: Unique identifier matching the request
            session_id: Session identifier for conversation tracking
            response: The response text from the LLM
            duration_seconds: Time taken for the request in seconds
            token_usage: Optional token usage statistics
            correlation_id: Optional correlation ID for linking operations
            timestamp: Optional timestamp (uses current time if not provided)
            status: Status of the response (success, error, etc.)
        
        Returns:
            JSON string representing the log entry
        """
        log_entry = {
            "log_type": "llm_response",
            "timestamp": timestamp or self._get_timestamp(),
            "request_id": request_id,
            "session_id": session_id,
            "correlation_id": correlation_id or request_id,
            "response": response,
            "response_length": len(response),
            "duration_seconds": round(duration_seconds, 3),
            "status": status
        }
        
        if token_usage:
            log_entry["token_usage"] = token_usage
        
        return json.dumps(log_entry, ensure_ascii=False)
    
    def format_llm_error(
        self,
        request_id: str,
        session_id: str,
        error_message: str,
        error_type: str,
        duration_seconds: float,
        correlation_id: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Format an LLM error as structured JSON.
        
        Args:
            request_id: Unique identifier matching the request
            session_id: Session identifier for conversation tracking
            error_message: The error message
            error_type: Type of error (e.g., exception class name)
            duration_seconds: Time taken before error occurred
            correlation_id: Optional correlation ID for linking operations
            timestamp: Optional timestamp (uses current time if not provided)
        
        Returns:
            JSON string representing the log entry
        """
        log_entry = {
            "log_type": "llm_response",
            "timestamp": timestamp or self._get_timestamp(),
            "request_id": request_id,
            "session_id": session_id,
            "correlation_id": correlation_id or request_id,
            "status": "error",
            "error_type": error_type,
            "error_message": error_message,
            "duration_seconds": round(duration_seconds, 3)
        }
        
        return json.dumps(log_entry, ensure_ascii=False)
    
    def format_reflection(
        self,
        session_id: str,
        reflection_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Format an agent reflection as structured JSON.
        
        Args:
            session_id: Session identifier for conversation tracking
            reflection_type: Type of reflection (query_analysis, tool_decision, etc.)
            data: Reflection-specific data
            correlation_id: Optional correlation ID for linking operations
            timestamp: Optional timestamp (uses current time if not provided)
        
        Returns:
            JSON string representing the log entry
        """
        log_entry = {
            "log_type": "agent_reflection",
            "timestamp": timestamp or self._get_timestamp(),
            "session_id": session_id,
            "correlation_id": correlation_id or session_id,
            "reflection_type": reflection_type,
            "data": data
        }
        
        return json.dumps(log_entry, ensure_ascii=False)
    
    def format_context_event(
        self,
        session_id: str,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Format a conversation context event as structured JSON.
        
        Args:
            session_id: Session identifier for conversation tracking
            event_type: Type of context event (message_added, truncation, reset)
            data: Event-specific data
            correlation_id: Optional correlation ID for linking operations
            timestamp: Optional timestamp (uses current time if not provided)
        
        Returns:
            JSON string representing the log entry
        """
        log_entry = {
            "log_type": "conversation_context",
            "timestamp": timestamp or self._get_timestamp(),
            "session_id": session_id,
            "correlation_id": correlation_id or session_id,
            "event_type": event_type,
            "data": data
        }
        
        return json.dumps(log_entry, ensure_ascii=False)
