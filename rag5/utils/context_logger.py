"""
Conversation context logging utilities for enhanced observability.

This module provides logging capabilities for tracking conversation history
evolution, including message additions, context truncations, and resets.
"""

import logging
from pathlib import Path
from typing import Optional

from rag5.utils.structured_formatter import StructuredLogFormatter
from rag5.utils.id_generator import generate_session_id
from rag5.utils.async_writer import AsyncLogWriter, register_async_writer

logger = logging.getLogger(__name__)


class ConversationContextLogger:
    """
    Logger for conversation context changes.
    
    Tracks the evolution of conversation history, including message additions,
    context truncations, and resets for debugging multi-turn conversations.
    
    Attributes:
        log_file: Path to the log file
        session_id: Session identifier for conversation tracking
    
    Example:
        >>> from rag5.utils.context_logger import ConversationContextLogger
        >>> 
        >>> logger = ConversationContextLogger(
        ...     log_file="logs/conversation_context.log",
        ...     session_id="session-123"
        ... )
        >>> 
        >>> # Log a message addition
        >>> logger.log_message_added(
        ...     role="user",
        ...     content_length=45,
        ...     total_messages=3,
        ...     total_tokens=150
        ... )
        >>> 
        >>> # Log context truncation
        >>> logger.log_context_truncation(
        ...     strategy="oldest_first",
        ...     messages_removed=2,
        ...     tokens_saved=100
        ... )
    """
    
    def __init__(
        self,
        log_file: str = "logs/conversation_context.log",
        session_id: Optional[str] = None,
        async_logging: bool = True,
        buffer_size: int = 100
    ):
        """
        Initialize the conversation context logger.
        
        Args:
            log_file: Path to the log file
            session_id: Session identifier (generates new one if not provided)
            async_logging: Whether to use async writing for performance
            buffer_size: Buffer size for async writing
        """
        self.log_file = log_file
        self.session_id = session_id or generate_session_id()
        self.formatter = StructuredLogFormatter()
        self.async_logging = async_logging
        
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
            logger.error(f"Failed to write to context log file: {e}", exc_info=True)
    
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
    
    def log_message_added(
        self,
        role: str,
        content_length: int,
        total_messages: int,
        total_tokens: int,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log when a message is added to conversation context.
        
        Args:
            role: Role of the message (user, assistant, system)
            content_length: Length of the message content in characters
            total_messages: Total number of messages in context after addition
            total_tokens: Estimated total tokens in context
            correlation_id: Optional correlation ID for linking operations
        """
        try:
            data = {
                "role": role,
                "content_length": content_length,
                "total_messages": total_messages,
                "total_tokens": total_tokens
            }
            
            log_entry = self.formatter.format_context_event(
                session_id=self.session_id,
                event_type="message_added",
                data=data,
                correlation_id=correlation_id
            )
            
            self._write_log(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log message addition: {e}", exc_info=True)
    
    def log_context_truncation(
        self,
        strategy: str,
        messages_removed: int,
        tokens_saved: int,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log when conversation context is truncated.
        
        Args:
            strategy: Truncation strategy used (e.g., "oldest_first", "sliding_window")
            messages_removed: Number of messages removed from context
            tokens_saved: Estimated number of tokens saved by truncation
            correlation_id: Optional correlation ID for linking operations
        """
        try:
            data = {
                "strategy": strategy,
                "messages_removed": messages_removed,
                "tokens_saved": tokens_saved
            }
            
            log_entry = self.formatter.format_context_event(
                session_id=self.session_id,
                event_type="context_truncation",
                data=data,
                correlation_id=correlation_id
            )
            
            self._write_log(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log context truncation: {e}", exc_info=True)
    
    def log_context_reset(
        self,
        trigger: str,
        final_size: int,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log when conversation context is reset.
        
        Args:
            trigger: What triggered the reset (e.g., "user_request", "max_length", "new_session")
            final_size: Number of messages remaining after reset
            correlation_id: Optional correlation ID for linking operations
        """
        try:
            data = {
                "trigger": trigger,
                "final_size": final_size
            }
            
            log_entry = self.formatter.format_context_event(
                session_id=self.session_id,
                event_type="context_reset",
                data=data,
                correlation_id=correlation_id
            )
            
            self._write_log(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log context reset: {e}", exc_info=True)
