"""
Sensitive data redaction utilities for privacy protection.

This module provides redaction capabilities to protect sensitive information
in logs while maintaining observability for debugging and analysis.
"""

import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)


class SensitiveDataRedactor:
    """
    Redacts sensitive data from log content.
    
    Provides configurable redaction of prompts, responses, and custom patterns
    while preserving error messages and diagnostic information for debugging.
    
    Attributes:
        redact_prompts: Whether to redact LLM prompts
        redact_responses: Whether to redact LLM responses
        patterns: List of regex patterns to match and redact
    
    Example:
        >>> from rag5.utils.redactor import SensitiveDataRedactor
        >>> 
        >>> # Create redactor with default settings
        >>> redactor = SensitiveDataRedactor(
        ...     redact_prompts=True,
        ...     redact_responses=False
        ... )
        >>> 
        >>> # Redact text
        >>> text = "User query: What is my account balance?"
        >>> redacted = redactor.redact_text(text)
        >>> print(redacted)
        [REDACTED: 42 characters]
        >>> 
        >>> # Check if redaction should apply
        >>> if redactor.should_redact("llm_request"):
        ...     print("Will redact this log type")
    """
    
    def __init__(
        self,
        redact_prompts: bool = False,
        redact_responses: bool = False,
        patterns: Optional[List[str]] = None
    ):
        """
        Initialize the sensitive data redactor.
        
        Args:
            redact_prompts: Whether to redact LLM prompts
            redact_responses: Whether to redact LLM responses
            patterns: Optional list of regex patterns to match and redact
        
        Example:
            >>> # Redact prompts only
            >>> redactor = SensitiveDataRedactor(redact_prompts=True)
            >>> 
            >>> # Redact with custom patterns
            >>> redactor = SensitiveDataRedactor(
            ...     redact_prompts=True,
            ...     patterns=[r'\b\d{3}-\d{2}-\d{4}\b']  # SSN pattern
            ... )
        """
        self.redact_prompts = redact_prompts
        self.redact_responses = redact_responses
        self.patterns = patterns or []
        
        # Compile regex patterns for efficiency
        self._compiled_patterns = []
        for pattern in self.patterns:
            try:
                self._compiled_patterns.append(re.compile(pattern))
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")
    
    def redact_text(self, text: str) -> str:
        """
        Redact sensitive information from text.
        
        Replaces the entire text with a placeholder indicating the original
        length, allowing analysts to understand the scale of redacted content
        without exposing sensitive information.
        
        Args:
            text: Text to redact
        
        Returns:
            Redacted text with length indicator
        
        Example:
            >>> redactor = SensitiveDataRedactor(redact_prompts=True)
            >>> original = "This is sensitive user data"
            >>> redacted = redactor.redact_text(original)
            >>> print(redacted)
            [REDACTED: 28 characters]
        """
        if not text:
            return text
        
        # Apply custom pattern redaction if patterns are defined
        redacted_text = text
        for pattern in self._compiled_patterns:
            redacted_text = pattern.sub(
                lambda m: f"[REDACTED: {len(m.group(0))} characters]",
                redacted_text
            )
        
        # If custom patterns were applied and changed the text, return it
        if redacted_text != text:
            return redacted_text
        
        # Otherwise, redact the entire text with length indicator
        return f"[REDACTED: {len(text)} characters]"
    
    def should_redact(self, log_type: str) -> bool:
        """
        Check if this log type should be redacted.
        
        Determines whether redaction should be applied based on the log type
        and configuration. Error messages and diagnostics are never redacted
        to preserve debugging capability.
        
        Args:
            log_type: Type of log entry (e.g., "llm_request", "llm_response", "llm_error")
        
        Returns:
            True if redaction should be applied, False otherwise
        
        Example:
            >>> redactor = SensitiveDataRedactor(redact_prompts=True)
            >>> redactor.should_redact("llm_request")
            True
            >>> redactor.should_redact("llm_error")
            False
        """
        # Never redact error messages or diagnostics
        if log_type in ("llm_error", "error", "diagnostic"):
            return False
        
        # Check if we should redact based on log type
        if log_type == "llm_request" and self.redact_prompts:
            return True
        
        if log_type == "llm_response" and self.redact_responses:
            return True
        
        # Check if custom patterns are defined (apply to all non-error types)
        if self._compiled_patterns:
            return True
        
        return False
    
    def redact_if_needed(self, text: str, log_type: str) -> str:
        """
        Conditionally redact text based on log type.
        
        Convenience method that combines should_redact() and redact_text()
        to simplify redaction logic in logging code.
        
        Args:
            text: Text to potentially redact
            log_type: Type of log entry
        
        Returns:
            Original text or redacted text based on configuration
        
        Example:
            >>> redactor = SensitiveDataRedactor(redact_prompts=True)
            >>> prompt = "What is my password?"
            >>> result = redactor.redact_if_needed(prompt, "llm_request")
            >>> print(result)
            [REDACTED: 20 characters]
            >>> 
            >>> error = "Connection timeout"
            >>> result = redactor.redact_if_needed(error, "llm_error")
            >>> print(result)
            Connection timeout
        """
        if self.should_redact(log_type):
            return self.redact_text(text)
        return text
