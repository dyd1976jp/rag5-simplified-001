"""
Agent reflection logging utilities for enhanced observability.

This module provides logging capabilities for agent reasoning processes,
including query analysis, tool decisions, query reformulation, retrieval
evaluation, and synthesis decisions.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from rag5.utils.structured_formatter import StructuredLogFormatter
from rag5.utils.id_generator import generate_correlation_id
from rag5.utils.async_writer import AsyncLogWriter, register_async_writer

logger = logging.getLogger(__name__)


class AgentReflectionLogger:
    """
    Logger for agent reasoning and decision-making processes.
    
    Captures the agent's internal reasoning, tool selection decisions,
    query reformulations, and document relevance assessments for
    debugging and understanding agent behavior.
    
    Attributes:
        log_file: Path to the reflection log file
        session_id: Session identifier for conversation tracking
        formatter: StructuredLogFormatter for JSON formatting
    
    Example:
        >>> from rag5.utils.reflection_logger import AgentReflectionLogger
        >>> 
        >>> logger = AgentReflectionLogger(
        ...     log_file="logs/agent_reflections.log",
        ...     session_id="session-123"
        ... )
        >>> 
        >>> # Log query analysis
        >>> logger.log_query_analysis(
        ...     original_query="李小勇和人合作入股了什么公司",
        ...     detected_intent="factual_lookup",
        ...     requires_tools=True,
        ...     reasoning="Query contains specific entity names"
        ... )
        >>> 
        >>> # Log tool decision
        >>> logger.log_tool_decision(
        ...     tool_name="search_knowledge_base",
        ...     decision_rationale="Need to search for factual information",
        ...     confidence=0.95
        ... )
    """
    
    def __init__(
        self,
        log_file: str = "logs/agent_reflections.log",
        session_id: Optional[str] = None,
        async_logging: bool = True,
        buffer_size: int = 100,
        max_entry_size: Optional[int] = None
    ):
        """
        Initialize the agent reflection logger.
        
        Args:
            log_file: Path to the reflection log file
            session_id: Optional session identifier for conversation tracking
            async_logging: Whether to use async writing for performance
            buffer_size: Buffer size for async writing
            max_entry_size: Maximum size in bytes for a single log entry
        """
        self.log_file = log_file
        self.session_id = session_id or generate_correlation_id("session")
        self.formatter = StructuredLogFormatter(max_entry_size=max_entry_size)
        self.async_logging = async_logging
        self.max_entry_size = max_entry_size
        
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
            logger.error(f"Failed to write to reflection log file: {e}", exc_info=True)
    
    def _truncate_text_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Truncate large text fields in reflection data.
        
        Args:
            data: Dictionary containing reflection data
        
        Returns:
            Dictionary with truncated text fields
        """
        if not self.max_entry_size:
            return data
        
        # Create a copy to avoid modifying the original
        truncated_data = data.copy()
        
        # Fields that may contain large text
        text_fields = ['reasoning', 'decision_rationale', 'relevance_assessment', 
                      'original_query', 'reformulated_query', 'query_context']
        
        for field in text_fields:
            if field in truncated_data and isinstance(truncated_data[field], str):
                original_size = len(truncated_data[field].encode('utf-8'))
                truncated_data[field] = self.formatter.truncate_if_needed(truncated_data[field])
                
                # Log warning if truncation occurred
                if original_size > self.max_entry_size:
                    logger.warning(
                        f"Agent reflection field '{field}' truncated from {original_size} bytes "
                        f"to fit within {self.max_entry_size} byte limit"
                    )
        
        return truncated_data
    
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
    
    def log_query_analysis(
        self,
        original_query: str,
        detected_intent: str,
        requires_tools: bool,
        reasoning: str,
        confidence: Optional[float] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log query analysis and intent detection.
        
        Args:
            original_query: The original user query
            detected_intent: The detected intent (e.g., "factual_lookup", "conversational")
            requires_tools: Whether tools are needed to answer the query
            reasoning: Explanation of the analysis
            confidence: Optional confidence score (0.0 to 1.0)
            correlation_id: Optional correlation ID for linking operations
        """
        try:
            data = {
                "original_query": original_query,
                "detected_intent": detected_intent,
                "requires_tools": requires_tools,
                "reasoning": reasoning
            }
            
            if confidence is not None:
                data["confidence"] = round(confidence, 3)
            
            # Apply size limiting to text fields
            data = self._truncate_text_fields(data)
            
            log_entry = self.formatter.format_reflection(
                session_id=self.session_id,
                reflection_type="query_analysis",
                data=data,
                correlation_id=correlation_id
            )
            
            self._write_log(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log query analysis: {e}", exc_info=True)
    
    def log_tool_decision(
        self,
        tool_name: str,
        decision_rationale: str,
        confidence: float,
        query_context: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log tool selection decision.
        
        Args:
            tool_name: Name of the selected tool
            decision_rationale: Explanation of why this tool was selected
            confidence: Confidence score for the decision (0.0 to 1.0)
            query_context: Optional context about the query
            correlation_id: Optional correlation ID for linking operations
        """
        try:
            data = {
                "tool_name": tool_name,
                "decision_rationale": decision_rationale,
                "confidence": round(confidence, 3)
            }
            
            if query_context:
                data["query_context"] = query_context
            
            # Apply size limiting to text fields
            data = self._truncate_text_fields(data)
            
            log_entry = self.formatter.format_reflection(
                session_id=self.session_id,
                reflection_type="tool_decision",
                data=data,
                correlation_id=correlation_id
            )
            
            self._write_log(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log tool decision: {e}", exc_info=True)
    
    def log_query_reformulation(
        self,
        original_query: str,
        reformulated_query: str,
        reasoning: str,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log query reformulation for optimization.
        
        Args:
            original_query: The original query
            reformulated_query: The reformulated/optimized query
            reasoning: Explanation of why and how the query was reformulated
            correlation_id: Optional correlation ID for linking operations
        """
        try:
            data = {
                "original_query": original_query,
                "reformulated_query": reformulated_query,
                "reasoning": reasoning
            }
            
            # Apply size limiting to text fields
            data = self._truncate_text_fields(data)
            
            log_entry = self.formatter.format_reflection(
                session_id=self.session_id,
                reflection_type="query_reformulation",
                data=data,
                correlation_id=correlation_id
            )
            
            self._write_log(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log query reformulation: {e}", exc_info=True)
    
    def log_retrieval_evaluation(
        self,
        query: str,
        results_count: int,
        top_scores: List[float],
        relevance_assessment: str,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log evaluation of retrieved documents.
        
        Args:
            query: The search query
            results_count: Number of results retrieved
            top_scores: List of top relevance scores
            relevance_assessment: Assessment of document relevance
            correlation_id: Optional correlation ID for linking operations
        """
        try:
            data = {
                "query": query,
                "results_count": results_count,
                "top_scores": [round(score, 3) for score in top_scores],
                "relevance_assessment": relevance_assessment
            }
            
            # Apply size limiting to text fields
            data = self._truncate_text_fields(data)
            
            log_entry = self.formatter.format_reflection(
                session_id=self.session_id,
                reflection_type="retrieval_evaluation",
                data=data,
                correlation_id=correlation_id
            )
            
            self._write_log(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log retrieval evaluation: {e}", exc_info=True)
    
    def log_synthesis_decision(
        self,
        sources_used: int,
        confidence: float,
        reasoning: str,
        has_sufficient_info: Optional[bool] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log answer synthesis decision.
        
        Args:
            sources_used: Number of sources used for synthesis
            confidence: Confidence in the synthesized answer (0.0 to 1.0)
            reasoning: Explanation of the synthesis decision
            has_sufficient_info: Optional flag indicating if sufficient information was available
            correlation_id: Optional correlation ID for linking operations
        """
        try:
            data = {
                "sources_used": sources_used,
                "confidence": round(confidence, 3),
                "reasoning": reasoning
            }
            
            if has_sufficient_info is not None:
                data["has_sufficient_info"] = has_sufficient_info
            
            # Apply size limiting to text fields
            data = self._truncate_text_fields(data)
            
            log_entry = self.formatter.format_reflection(
                session_id=self.session_id,
                reflection_type="synthesis_decision",
                data=data,
                correlation_id=correlation_id
            )
            
            self._write_log(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log synthesis decision: {e}", exc_info=True)
