"""
Unit tests for FlowLogger.

Tests the flow logger functionality including event logging methods,
elapsed time calculation, error handling, and async writing.
"""

import pytest
import tempfile
import os
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from rag5.utils.flow_logger import FlowLogger


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_file = f.name
    yield log_file
    # Cleanup
    if os.path.exists(log_file):
        os.unlink(log_file)


class TestFlowLoggerInitialization:
    """Tests for FlowLogger initialization"""
    
    def test_default_initialization(self, temp_log_file):
        """Test logger with default parameters"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False  # Disable async for testing
        )
        
        assert logger.log_file == temp_log_file
        assert logger.session_id == "test-session"
        assert logger.enabled is True
        assert logger.detail_level == "normal"
        assert logger.max_content_length == 500
        assert logger.async_logging is False
        assert logger._start_time is None
    
    def test_custom_initialization(self, temp_log_file):
        """Test logger with custom parameters"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            enabled=True,
            detail_level="verbose",
            max_content_length=1000,
            async_logging=False
        )
        
        assert logger.detail_level == "verbose"
        assert logger.max_content_length == 1000
    
    def test_disabled_logger(self, temp_log_file):
        """Test that disabled logger doesn't write"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            enabled=False,
            async_logging=False
        )
        
        logger.log_query_start("Test query")
        
        # File should not be created
        assert not os.path.exists(temp_log_file) or os.path.getsize(temp_log_file) == 0


class TestElapsedTimeTracking:
    """Tests for elapsed time calculation"""
    
    def test_elapsed_time_before_query_start(self, temp_log_file):
        """Test that elapsed time is 0 before query starts"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        elapsed = logger.get_elapsed_time()
        
        assert elapsed == 0.0
    
    def test_elapsed_time_after_query_start(self, temp_log_file):
        """Test that elapsed time increases after query start"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        logger.log_query_start("Test query")
        time.sleep(0.1)
        elapsed = logger.get_elapsed_time()
        
        assert elapsed >= 0.1
        assert elapsed < 0.2  # Should be close to 0.1
    
    def test_elapsed_time_resets_on_new_query(self, temp_log_file):
        """Test that elapsed time resets when new query starts"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        logger.log_query_start("First query")
        time.sleep(0.1)
        first_elapsed = logger.get_elapsed_time()
        
        logger.log_query_start("Second query")
        second_elapsed = logger.get_elapsed_time()
        
        assert first_elapsed >= 0.1
        assert second_elapsed < first_elapsed


class TestQueryStartLogging:
    """Tests for log_query_start method"""
    
    def test_log_query_start_writes_to_file(self, temp_log_file):
        """Test that query start is written to file"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        logger.log_query_start("What is machine learning?")
        
        # Read log file
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "QUERY_START" in content
        assert "test-session" in content
        assert "What is machine learning?" in content
    
    def test_log_query_start_with_custom_timestamp(self, temp_log_file):
        """Test query start with custom timestamp"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        custom_time = datetime(2025, 11, 10, 14, 30, 45, 123000)
        logger.log_query_start("Test query", timestamp=custom_time)
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "2025-11-10 14:30:45.123" in content
    
    def test_log_query_start_sets_start_time(self, temp_log_file):
        """Test that query start sets the start time"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        assert logger._start_time is None
        
        logger.log_query_start("Test query")
        
        assert logger._start_time is not None
        assert isinstance(logger._start_time, float)


class TestQueryAnalysisLogging:
    """Tests for log_query_analysis method"""
    
    def test_log_query_analysis(self, temp_log_file):
        """Test query analysis logging"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        logger.log_query_start("Test query")
        logger.log_query_analysis(
            detected_intent="factual_lookup",
            requires_tools=True,
            reasoning="Query asks for factual information",
            confidence=0.95
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "QUERY_ANALYSIS" in content or "ANALYSIS" in content
        assert "factual_lookup" in content
        assert "Query asks for factual information" in content


class TestToolSelectionLogging:
    """Tests for log_tool_selection method"""
    
    def test_log_tool_selection(self, temp_log_file):
        """Test tool selection logging"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        logger.log_query_start("Test query")
        logger.log_tool_selection(
            tool_name="search_knowledge_base",
            rationale="Need to search for information",
            confidence=0.90
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "TOOL_SELECTION" in content or "TOOL_SELECT" in content
        assert "search_knowledge_base" in content
        assert "Need to search for information" in content


class TestToolExecutionLogging:
    """Tests for log_tool_execution method"""
    
    def test_log_tool_execution_success(self, temp_log_file):
        """Test successful tool execution logging"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        logger.log_query_start("Test query")
        logger.log_tool_execution(
            tool_name="search",
            tool_input="machine learning",
            tool_output="Found 5 documents",
            duration_seconds=0.456,
            status="success"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "TOOL_EXECUTION" in content or "TOOL_EXEC" in content
        assert "search" in content
        assert "machine learning" in content
        assert "Found 5 documents" in content
        assert "SUCCESS" in content
    
    def test_log_tool_execution_error(self, temp_log_file):
        """Test error tool execution logging"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        logger.log_query_start("Test query")
        logger.log_tool_execution(
            tool_name="search",
            tool_input="query",
            tool_output="Connection failed",
            duration_seconds=0.1,
            status="error"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "ERROR" in content
        assert "Connection failed" in content


class TestLLMCallLogging:
    """Tests for log_llm_call method"""
    
    def test_log_llm_call_with_tokens(self, temp_log_file):
        """Test LLM call logging with token usage"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        logger.log_query_start("Test query")
        logger.log_llm_call(
            model="qwen2.5:7b",
            prompt="What is AI?",
            response="AI is artificial intelligence",
            duration_seconds=2.345,
            token_usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            status="success"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "LLM_CALL" in content
        assert "qwen2.5:7b" in content
        assert "What is AI?" in content
        assert "AI is artificial intelligence" in content
        assert "SUCCESS" in content
    
    def test_log_llm_call_without_tokens(self, temp_log_file):
        """Test LLM call logging without token usage"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        logger.log_query_start("Test query")
        logger.log_llm_call(
            model="qwen2.5:7b",
            prompt="What is AI?",
            response="AI is artificial intelligence",
            duration_seconds=2.345,
            token_usage=None,
            status="success"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "LLM_CALL" in content
        assert "qwen2.5:7b" in content


class TestErrorLogging:
    """Tests for log_error method"""
    
    def test_log_error_with_stack_trace(self, temp_log_file):
        """Test error logging with stack trace"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        logger.log_query_start("Test query")
        logger.log_error(
            error_type="ValueError",
            error_message="Invalid input",
            stack_trace="Traceback (most recent call last):\n  File 'test.py', line 10"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "ERROR" in content
        assert "ValueError" in content
        assert "Invalid input" in content
        assert "Traceback" in content
    
    def test_log_error_without_stack_trace(self, temp_log_file):
        """Test error logging without stack trace"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        logger.log_query_start("Test query")
        logger.log_error(
            error_type="ValueError",
            error_message="Invalid input",
            stack_trace=None
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "ERROR" in content
        assert "ValueError" in content
        assert "Invalid input" in content


class TestQueryCompleteLogging:
    """Tests for log_query_complete method"""
    
    def test_log_query_complete_success(self, temp_log_file):
        """Test successful query completion logging"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        logger.log_query_start("Test query")
        time.sleep(0.1)
        logger.log_query_complete(
            final_answer="The answer is 42",
            total_duration_seconds=logger.get_elapsed_time(),
            status="success"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "QUERY_COMPLETE" in content or "COMPLETE" in content
        assert "test-session" in content
        assert "SUCCESS" in content
        assert "The answer is 42" in content
    
    def test_log_query_complete_error(self, temp_log_file):
        """Test error query completion logging"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        logger.log_query_start("Test query")
        logger.log_query_complete(
            final_answer="",
            total_duration_seconds=logger.get_elapsed_time(),
            status="error"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "ERROR" in content


class TestErrorHandling:
    """Tests for error handling and graceful degradation"""
    
    def test_logging_failure_does_not_raise(self, temp_log_file):
        """Test that logging failures don't raise exceptions"""
        logger = FlowLogger(
            log_file="/invalid/path/that/does/not/exist.log",
            session_id="test-session",
            async_logging=False
        )
        
        # Should not raise exception
        logger.log_query_start("Test query")
        logger.log_query_complete("Answer", 1.0, "success")
    
    def test_formatter_error_does_not_raise(self, temp_log_file):
        """Test that formatter errors don't raise exceptions"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        # Mock formatter to raise exception
        logger.formatter.format_query_start = Mock(side_effect=Exception("Test error"))
        
        # Should not raise exception
        logger.log_query_start("Test query")


class TestFlush:
    """Tests for flush method"""
    
    def test_flush_with_async_writer(self, temp_log_file):
        """Test flush with async writer"""
        with patch('rag5.utils.flow_logger.AsyncLogWriter') as mock_writer_class:
            mock_writer = Mock()
            mock_writer_class.return_value = mock_writer
            
            logger = FlowLogger(
                log_file=temp_log_file,
                session_id="test-session",
                async_logging=True
            )
            
            logger.flush()
            
            # Verify flush was called
            mock_writer.flush.assert_called_once()
    
    def test_flush_without_async_writer(self, temp_log_file):
        """Test flush without async writer"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            async_logging=False
        )
        
        # Should not raise exception
        logger.flush()


class TestDetailLevels:
    """Tests for different detail levels"""
    
    def test_minimal_detail_level(self, temp_log_file):
        """Test logging with minimal detail level"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            detail_level="minimal",
            async_logging=False
        )
        
        logger.log_query_start("Test query")
        logger.log_query_complete("Answer", 1.0, "success")
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Minimal format should be more compact
        assert content.count('\n') < 10
    
    def test_verbose_detail_level(self, temp_log_file):
        """Test logging with verbose detail level"""
        logger = FlowLogger(
            log_file=temp_log_file,
            session_id="test-session",
            detail_level="verbose",
            max_content_length=50,
            async_logging=False
        )
        
        long_query = "A" * 100
        logger.log_query_start(long_query)
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verbose mode should not truncate
        assert long_query in content
        assert "[Full length:" not in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
