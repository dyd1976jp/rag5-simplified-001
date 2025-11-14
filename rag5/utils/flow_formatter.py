"""
Flow formatter for human-readable unified logging.

This module provides formatting for unified flow logs that capture the complete
processing flow of each user query in a single, chronologically ordered format.
"""

from datetime import datetime
from typing import Optional, Dict, Any


class FlowFormatter:
    """
    Formatter for human-readable flow log entries.
    
    Converts flow events into well-formatted, easy-to-read text entries
    with proper indentation, visual separators, and content truncation.
    
    Supports three detail levels:
    - minimal: Single-line entries with key info only
    - normal: Multi-line with visual separators (default)
    - verbose: Full content without truncation
    
    Attributes:
        detail_level: Level of detail for formatting
        max_content_length: Maximum content length before truncation
        indent_size: Number of spaces per indentation level
        
    Example:
        >>> from rag5.utils.flow_formatter import FlowFormatter
        >>> 
        >>> # Create formatter with normal detail level
        >>> formatter = FlowFormatter(
        ...     detail_level="normal",
        ...     max_content_length=500
        ... )
        >>> 
        >>> # Format a query start event
        >>> entry = formatter.format_query_start(
        ...     session_id="abc-123",
        ...     query="What is the capital of France?",
        ...     timestamp=datetime.now()
        ... )
        >>> print(entry)
    """
    
    # Visual separators for different detail levels
    SEPARATOR_FULL = "=" * 80
    SEPARATOR_HALF = "-" * 80
    
    def __init__(
        self,
        detail_level: str = "normal",
        max_content_length: int = 500,
        indent_size: int = 2
    ):
        """
        Initialize the flow formatter.
        
        Args:
            detail_level: Level of detail ("minimal", "normal", "verbose")
            max_content_length: Maximum content length before truncation
            indent_size: Number of spaces per indentation level
        """
        if detail_level not in ("minimal", "normal", "verbose"):
            raise ValueError(
                f"Invalid detail_level: {detail_level}. "
                "Must be 'minimal', 'normal', or 'verbose'"
            )
        
        self.detail_level = detail_level
        self.max_content_length = max_content_length
        self.indent_size = indent_size
    
    def _format_timestamp(self, timestamp: datetime) -> str:
        """
        Format timestamp consistently.
        
        Args:
            timestamp: Datetime object to format
            
        Returns:
            Formatted timestamp string (e.g., "2025-11-10 14:30:45.123")
        """
        return timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def truncate_content(self, content: str, max_length: Optional[int] = None) -> str:
        """
        Truncate content if it exceeds max length.
        
        Args:
            content: Content to truncate
            max_length: Maximum allowed length (uses instance default if None)
            
        Returns:
            Truncated content with indicator if truncated
        """
        # In verbose mode, never truncate
        if self.detail_level == "verbose":
            return content
        
        # Use provided max_length or instance default
        limit = max_length if max_length is not None else self.max_content_length
        
        if len(content) <= limit:
            return content
        
        # Truncate and add indicator
        truncated = content[:limit]
        indicator = f"\n  [Full length: {len(content)} chars]"
        return truncated + indicator
    
    def apply_indentation(self, text: str, level: int) -> str:
        """
        Apply indentation to text.
        
        Args:
            text: Text to indent
            level: Indentation level
            
        Returns:
            Indented text
        """
        if level <= 0:
            return text
        
        indent = " " * (self.indent_size * level)
        lines = text.split("\n")
        return "\n".join(indent + line if line.strip() else line for line in lines)

    def format_query_start(
        self,
        session_id: str,
        query: str,
        timestamp: datetime
    ) -> str:
        """
        Format query start entry.
        
        Args:
            session_id: Unique session identifier
            query: The user's query
            timestamp: Event timestamp
            
        Returns:
            Formatted log entry string
        """
        ts = self._format_timestamp(timestamp)
        
        if self.detail_level == "minimal":
            # Single-line format
            query_preview = query[:50] + "..." if len(query) > 50 else query
            return f"[{ts}] QUERY_START ({session_id}) Query: {query_preview}"
        
        # Normal and verbose formats
        lines = [
            self.SEPARATOR_FULL,
            f"[{ts}] QUERY_START (Session: {session_id}) [+0.000s]",
            self.SEPARATOR_HALF,
            f"Query: {self.truncate_content(query)}",
            self.SEPARATOR_FULL
        ]
        return "\n".join(lines)
    
    def format_query_analysis(
        self,
        detected_intent: str,
        requires_tools: bool,
        reasoning: str,
        confidence: float,
        elapsed_time: float
    ) -> str:
        """
        Format query analysis entry.
        
        Args:
            detected_intent: The detected intent type
            requires_tools: Whether tools are needed
            reasoning: Explanation of the analysis
            confidence: Confidence score (0-1)
            elapsed_time: Time elapsed since query start
            
        Returns:
            Formatted log entry string
        """
        if self.detail_level == "minimal":
            # Single-line format
            tools_str = "Yes" if requires_tools else "No"
            return (
                f"[+{elapsed_time:.3f}s] ANALYSIS "
                f"Intent: {detected_intent}, Tools: {tools_str}"
            )
        
        # Normal and verbose formats
        timestamp = datetime.now()
        ts = self._format_timestamp(timestamp)
        
        lines = [
            "",
            self.SEPARATOR_FULL,
            f"[{ts}] QUERY_ANALYSIS [+{elapsed_time:.3f}s]",
            self.SEPARATOR_HALF,
            f"Detected Intent: {detected_intent}",
            f"Requires Tools: {'Yes' if requires_tools else 'No'}",
            f"Confidence: {confidence:.2f}",
            "",
            "Reasoning:",
            self.apply_indentation(self.truncate_content(reasoning), 1),
            self.SEPARATOR_FULL
        ]
        return "\n".join(lines)
    
    def format_tool_selection(
        self,
        tool_name: str,
        rationale: str,
        confidence: float,
        elapsed_time: float
    ) -> str:
        """
        Format tool selection entry.
        
        Args:
            tool_name: Name of the selected tool
            rationale: Reason for selecting this tool
            confidence: Confidence in the selection (0-1)
            elapsed_time: Time elapsed since query start
            
        Returns:
            Formatted log entry string
        """
        if self.detail_level == "minimal":
            # Single-line format
            return f"[+{elapsed_time:.3f}s] TOOL_SELECT {tool_name}"
        
        # Normal and verbose formats
        timestamp = datetime.now()
        ts = self._format_timestamp(timestamp)
        
        lines = [
            "",
            self.SEPARATOR_FULL,
            f"[{ts}] TOOL_SELECTION [+{elapsed_time:.3f}s]",
            self.SEPARATOR_HALF,
            f"Selected Tool: {tool_name}",
            f"Confidence: {confidence:.2f}",
            "",
            "Rationale:",
            self.apply_indentation(self.truncate_content(rationale), 1),
            self.SEPARATOR_FULL
        ]
        return "\n".join(lines)
    
    def format_tool_execution(
        self,
        tool_name: str,
        tool_input: str,
        tool_output: str,
        duration_seconds: float,
        elapsed_time: float,
        status: str
    ) -> str:
        """
        Format tool execution entry.
        
        Args:
            tool_name: Name of the tool
            tool_input: Input provided to the tool
            tool_output: Output from the tool
            duration_seconds: Execution time
            elapsed_time: Time elapsed since query start
            status: Execution status ("success" or "error")
            
        Returns:
            Formatted log entry string
        """
        if self.detail_level == "minimal":
            # Single-line format
            status_str = "SUCCESS" if status == "success" else "ERROR"
            output_preview = tool_output[:30] + "..." if len(tool_output) > 30 else tool_output
            return (
                f"[+{elapsed_time:.3f}s] TOOL_EXEC {tool_name} "
                f"[{duration_seconds:.3f}s] {status_str}: {output_preview}"
            )
        
        # Normal and verbose formats
        timestamp = datetime.now()
        ts = self._format_timestamp(timestamp)
        status_upper = status.upper()
        
        lines = [
            "",
            self.SEPARATOR_FULL,
            f"[{ts}] TOOL_EXECUTION [+{elapsed_time:.3f}s]",
            self.SEPARATOR_HALF,
            f"Tool: {tool_name}",
            f"Status: {status_upper}",
            f"Duration: {duration_seconds:.3f}s",
            "",
            "Input:",
            self.apply_indentation(self.truncate_content(tool_input), 1),
            "",
            "Output:",
            self.apply_indentation(self.truncate_content(tool_output), 1),
            self.SEPARATOR_FULL
        ]
        return "\n".join(lines)
    
    def format_llm_call(
        self,
        model: str,
        prompt: str,
        response: str,
        duration_seconds: float,
        elapsed_time: float,
        token_usage: Optional[Dict[str, int]],
        status: str
    ) -> str:
        """
        Format LLM call entry.
        
        Args:
            model: Model name
            prompt: Prompt sent to LLM
            response: Response from LLM
            duration_seconds: Call duration
            elapsed_time: Time elapsed since query start
            token_usage: Token usage statistics
            status: Call status ("success" or "error")
            
        Returns:
            Formatted log entry string
        """
        if self.detail_level == "minimal":
            # Single-line format
            status_str = "SUCCESS" if status == "success" else "ERROR"
            tokens_str = ""
            if token_usage:
                total = token_usage.get("total_tokens", 0)
                tokens_str = f" {total} tokens"
            return (
                f"[+{elapsed_time:.3f}s] LLM_CALL {model} "
                f"[{duration_seconds:.3f}s]{tokens_str} {status_str}"
            )
        
        # Normal and verbose formats
        timestamp = datetime.now()
        ts = self._format_timestamp(timestamp)
        status_upper = status.upper()
        
        lines = [
            "",
            self.SEPARATOR_FULL,
            f"[{ts}] LLM_CALL [+{elapsed_time:.3f}s]",
            self.SEPARATOR_HALF,
            f"Model: {model}",
            f"Status: {status_upper}",
            f"Duration: {duration_seconds:.3f}s"
        ]
        
        # Add token usage if available
        if token_usage:
            prompt_tokens = token_usage.get("prompt_tokens", 0)
            completion_tokens = token_usage.get("completion_tokens", 0)
            total_tokens = token_usage.get("total_tokens", 0)
            lines.append(
                f"Tokens: {prompt_tokens} prompt + {completion_tokens} completion = {total_tokens} total"
            )
        
        # Add prompt and response
        prompt_truncated = self.truncate_content(prompt)
        response_truncated = self.truncate_content(response)
        
        lines.extend([
            "",
            f"Prompt (truncated to {self.max_content_length} chars):" if len(prompt) > self.max_content_length else "Prompt:",
            self.apply_indentation(prompt_truncated, 1),
            "",
            f"Response (truncated to {self.max_content_length} chars):" if len(response) > self.max_content_length else "Response:",
            self.apply_indentation(response_truncated, 1),
            self.SEPARATOR_FULL
        ])
        
        return "\n".join(lines)
    
    def format_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str],
        elapsed_time: float
    ) -> str:
        """
        Format error entry.
        
        Args:
            error_type: Type of error
            error_message: Error message
            stack_trace: Optional stack trace
            elapsed_time: Time elapsed since query start
            
        Returns:
            Formatted log entry string
        """
        if self.detail_level == "minimal":
            # Single-line format
            msg_preview = error_message[:50] + "..." if len(error_message) > 50 else error_message
            return f"[+{elapsed_time:.3f}s] ERROR {error_type}: {msg_preview}"
        
        # Normal and verbose formats
        timestamp = datetime.now()
        ts = self._format_timestamp(timestamp)
        
        lines = [
            "",
            self.SEPARATOR_FULL,
            f"[{ts}] ERROR [+{elapsed_time:.3f}s]",
            self.SEPARATOR_HALF,
            f"Error Type: {error_type}",
            f"Message: {error_message}"
        ]
        
        # Add stack trace if available
        if stack_trace:
            lines.extend([
                "",
                "Stack Trace:",
                self.apply_indentation(self.truncate_content(stack_trace, max_length=1000), 1)
            ])
        
        lines.append(self.SEPARATOR_FULL)
        return "\n".join(lines)
    
    def format_query_complete(
        self,
        session_id: str,
        final_answer: str,
        total_duration_seconds: float,
        status: str
    ) -> str:
        """
        Format query completion entry.
        
        Args:
            session_id: Unique session identifier
            final_answer: The final answer provided to user
            total_duration_seconds: Total processing time
            status: Final status ("success" or "error")
            
        Returns:
            Formatted log entry string
        """
        if self.detail_level == "minimal":
            # Single-line format
            status_str = "SUCCESS" if status == "success" else "ERROR"
            return (
                f"[+{total_duration_seconds:.3f}s] COMPLETE ({session_id}) "
                f"{status_str} [{total_duration_seconds:.3f}s total]"
            )
        
        # Normal and verbose formats
        timestamp = datetime.now()
        ts = self._format_timestamp(timestamp)
        status_upper = status.upper()
        
        lines = [
            "",
            self.SEPARATOR_FULL,
            f"[{ts}] QUERY_COMPLETE (Session: {session_id}) [+{total_duration_seconds:.3f}s]",
            self.SEPARATOR_HALF,
            f"Status: {status_upper}",
            f"Total Duration: {total_duration_seconds:.3f}s"
        ]
        
        # Add final answer if status is success
        if status == "success" and final_answer:
            lines.extend([
                "",
                "Final Answer:",
                self.apply_indentation(self.truncate_content(final_answer), 1)
            ])
        
        lines.append(self.SEPARATOR_FULL)
        return "\n".join(lines)
