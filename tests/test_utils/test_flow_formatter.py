"""
Unit tests for FlowFormatter.

Tests the formatting of flow log entries with different detail levels,
content truncation, indentation, and timestamp formatting.
"""

import pytest
from datetime import datetime

from rag5.utils.flow_formatter import FlowFormatter


class TestFlowFormatterInitialization:
    """Tests for FlowFormatter initialization"""
    
    def test_default_initialization(self):
        """Test formatter with default parameters"""
        formatter = FlowFormatter()
        
        assert formatter.detail_level == "normal"
        assert formatter.max_content_length == 500
        assert formatter.indent_size == 2
    
    def test_custom_initialization(self):
        """Test formatter with custom parameters"""
        formatter = FlowFormatter(
            detail_level="verbose",
            max_content_length=1000,
            indent_size=4
        )
        
        assert formatter.detail_level == "verbose"
        assert formatter.max_content_length == 1000
        assert formatter.indent_size == 4
    
    def test_invalid_detail_level(self):
        """Test that invalid detail level raises error"""
        with pytest.raises(ValueError, match="Invalid detail_level"):
            FlowFormatter(detail_level="invalid")


class TestContentTruncation:
    """Tests for content truncation"""
    
    def test_no_truncation_when_under_limit(self):
        """Test that short content is not truncated"""
        formatter = FlowFormatter(max_content_length=100)
        content = "Short content"
        
        result = formatter.truncate_content(content)
        
        assert result == content
        assert "[Full length:" not in result
    
    def test_truncation_when_over_limit(self):
        """Test that long content is truncated"""
        formatter = FlowFormatter(max_content_length=50)
        content = "A" * 100
        
        result = formatter.truncate_content(content)
        
        assert len(result) < len(content)
        assert result.startswith("A" * 50)
        assert "[Full length: 100 chars]" in result
    
    def test_no_truncation_in_verbose_mode(self):
        """Test that verbose mode never truncates"""
        formatter = FlowFormatter(detail_level="verbose", max_content_length=50)
        content = "A" * 100
        
        result = formatter.truncate_content(content)
        
        assert result == content
        assert "[Full length:" not in result
    
    def test_custom_max_length(self):
        """Test truncation with custom max length"""
        formatter = FlowFormatter(max_content_length=100)
        content = "A" * 200
        
        result = formatter.truncate_content(content, max_length=50)
        
        assert result.startswith("A" * 50)
        assert "[Full length: 200 chars]" in result


class TestIndentation:
    """Tests for text indentation"""
    
    def test_no_indentation_at_level_zero(self):
        """Test that level 0 adds no indentation"""
        formatter = FlowFormatter()
        text = "Line 1\nLine 2"
        
        result = formatter.apply_indentation(text, level=0)
        
        assert result == text
    
    def test_single_level_indentation(self):
        """Test single level indentation"""
        formatter = FlowFormatter(indent_size=2)
        text = "Line 1\nLine 2"
        
        result = formatter.apply_indentation(text, level=1)
        
        assert result == "  Line 1\n  Line 2"
    
    def test_multiple_level_indentation(self):
        """Test multiple level indentation"""
        formatter = FlowFormatter(indent_size=2)
        text = "Line 1\nLine 2"
        
        result = formatter.apply_indentation(text, level=2)
        
        assert result == "    Line 1\n    Line 2"
    
    def test_custom_indent_size(self):
        """Test indentation with custom indent size"""
        formatter = FlowFormatter(indent_size=4)
        text = "Line 1"
        
        result = formatter.apply_indentation(text, level=1)
        
        assert result == "    Line 1"
    
    def test_empty_lines_preserved(self):
        """Test that empty lines are preserved"""
        formatter = FlowFormatter(indent_size=2)
        text = "Line 1\n\nLine 2"
        
        result = formatter.apply_indentation(text, level=1)
        
        assert "\n\n" in result


class TestTimestampFormatting:
    """Tests for timestamp formatting"""
    
    def test_timestamp_format(self):
        """Test timestamp formatting"""
        formatter = FlowFormatter()
        timestamp = datetime(2025, 11, 10, 14, 30, 45, 123456)
        
        result = formatter._format_timestamp(timestamp)
        
        assert result == "2025-11-10 14:30:45.123"
    
    def test_timestamp_milliseconds(self):
        """Test that milliseconds are included"""
        formatter = FlowFormatter()
        timestamp = datetime(2025, 11, 10, 14, 30, 45, 999000)
        
        result = formatter._format_timestamp(timestamp)
        
        assert result.endswith(".999")


class TestQueryStartFormatting:
    """Tests for query start entry formatting"""
    
    def test_minimal_format(self):
        """Test minimal detail level format"""
        formatter = FlowFormatter(detail_level="minimal")
        timestamp = datetime(2025, 11, 10, 14, 30, 45, 123000)
        
        result = formatter.format_query_start(
            session_id="test-123",
            query="What is machine learning?",
            timestamp=timestamp
        )
        
        assert "[2025-11-10 14:30:45.123]" in result
        assert "QUERY_START" in result
        assert "test-123" in result
        assert "What is machine learning?" in result
        assert "\n" not in result  # Single line
    
    def test_minimal_format_long_query(self):
        """Test minimal format truncates long queries"""
        formatter = FlowFormatter(detail_level="minimal")
        timestamp = datetime.now()
        long_query = "A" * 100
        
        result = formatter.format_query_start(
            session_id="test-123",
            query=long_query,
            timestamp=timestamp
        )
        
        assert "..." in result
        assert len(result) < len(long_query) + 100
    
    def test_normal_format(self):
        """Test normal detail level format"""
        formatter = FlowFormatter(detail_level="normal")
        timestamp = datetime(2025, 11, 10, 14, 30, 45, 123000)
        
        result = formatter.format_query_start(
            session_id="test-123",
            query="What is machine learning?",
            timestamp=timestamp
        )
        
        assert "=" * 80 in result
        assert "[2025-11-10 14:30:45.123]" in result
        assert "QUERY_START" in result
        assert "Session: test-123" in result
        assert "[+0.000s]" in result
        assert "Query: What is machine learning?" in result
    
    def test_verbose_format(self):
        """Test verbose detail level format"""
        formatter = FlowFormatter(detail_level="verbose")
        timestamp = datetime.now()
        long_query = "A" * 1000
        
        result = formatter.format_query_start(
            session_id="test-123",
            query=long_query,
            timestamp=timestamp
        )
        
        # Verbose mode should not truncate
        assert long_query in result
        assert "[Full length:" not in result


class TestQueryAnalysisFormatting:
    """Tests for query analysis entry formatting"""
    
    def test_minimal_format(self):
        """Test minimal format"""
        formatter = FlowFormatter(detail_level="minimal")
        
        result = formatter.format_query_analysis(
            detected_intent="factual_lookup",
            requires_tools=True,
            reasoning="Query asks for factual information",
            confidence=0.95,
            elapsed_time=0.123
        )
        
        assert "[+0.123s]" in result
        assert "ANALYSIS" in result
        assert "factual_lookup" in result
        assert "Yes" in result
    
    def test_normal_format(self):
        """Test normal format"""
        formatter = FlowFormatter(detail_level="normal")
        
        result = formatter.format_query_analysis(
            detected_intent="factual_lookup",
            requires_tools=True,
            reasoning="Query asks for factual information",
            confidence=0.95,
            elapsed_time=0.123
        )
        
        assert "QUERY_ANALYSIS" in result
        assert "[+0.123s]" in result
        assert "Detected Intent: factual_lookup" in result
        assert "Requires Tools: Yes" in result
        assert "Confidence: 0.95" in result
        assert "Reasoning:" in result
        assert "Query asks for factual information" in result


class TestToolSelectionFormatting:
    """Tests for tool selection entry formatting"""
    
    def test_minimal_format(self):
        """Test minimal format"""
        formatter = FlowFormatter(detail_level="minimal")
        
        result = formatter.format_tool_selection(
            tool_name="search_knowledge_base",
            rationale="Need to search for information",
            confidence=0.90,
            elapsed_time=0.234
        )
        
        assert "[+0.234s]" in result
        assert "TOOL_SELECT" in result
        assert "search_knowledge_base" in result
    
    def test_normal_format(self):
        """Test normal format"""
        formatter = FlowFormatter(detail_level="normal")
        
        result = formatter.format_tool_selection(
            tool_name="search_knowledge_base",
            rationale="Need to search for information",
            confidence=0.90,
            elapsed_time=0.234
        )
        
        assert "TOOL_SELECTION" in result
        assert "[+0.234s]" in result
        assert "Selected Tool: search_knowledge_base" in result
        assert "Confidence: 0.90" in result
        assert "Rationale:" in result
        assert "Need to search for information" in result


class TestToolExecutionFormatting:
    """Tests for tool execution entry formatting"""
    
    def test_minimal_format_success(self):
        """Test minimal format for successful execution"""
        formatter = FlowFormatter(detail_level="minimal")
        
        result = formatter.format_tool_execution(
            tool_name="search",
            tool_input="machine learning",
            tool_output="Found 5 documents",
            duration_seconds=0.456,
            elapsed_time=0.789,
            status="success"
        )
        
        assert "[+0.789s]" in result
        assert "TOOL_EXEC" in result
        assert "search" in result
        assert "[0.456s]" in result
        assert "SUCCESS" in result
    
    def test_minimal_format_error(self):
        """Test minimal format for error"""
        formatter = FlowFormatter(detail_level="minimal")
        
        result = formatter.format_tool_execution(
            tool_name="search",
            tool_input="query",
            tool_output="Connection failed",
            duration_seconds=0.1,
            elapsed_time=0.5,
            status="error"
        )
        
        assert "ERROR" in result
    
    def test_normal_format(self):
        """Test normal format"""
        formatter = FlowFormatter(detail_level="normal")
        
        result = formatter.format_tool_execution(
            tool_name="search",
            tool_input="machine learning",
            tool_output="Found 5 documents",
            duration_seconds=0.456,
            elapsed_time=0.789,
            status="success"
        )
        
        assert "TOOL_EXECUTION" in result
        assert "[+0.789s]" in result
        assert "Tool: search" in result
        assert "Status: SUCCESS" in result
        assert "Duration: 0.456s" in result
        assert "Input:" in result
        assert "machine learning" in result
        assert "Output:" in result
        assert "Found 5 documents" in result


class TestLLMCallFormatting:
    """Tests for LLM call entry formatting"""
    
    def test_minimal_format_with_tokens(self):
        """Test minimal format with token usage"""
        formatter = FlowFormatter(detail_level="minimal")
        
        result = formatter.format_llm_call(
            model="qwen2.5:7b",
            prompt="What is AI?",
            response="AI is...",
            duration_seconds=2.345,
            elapsed_time=3.456,
            token_usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            status="success"
        )
        
        assert "[+3.456s]" in result
        assert "LLM_CALL" in result
        assert "qwen2.5:7b" in result
        assert "[2.345s]" in result
        assert "30 tokens" in result
        assert "SUCCESS" in result
    
    def test_minimal_format_without_tokens(self):
        """Test minimal format without token usage"""
        formatter = FlowFormatter(detail_level="minimal")
        
        result = formatter.format_llm_call(
            model="qwen2.5:7b",
            prompt="What is AI?",
            response="AI is...",
            duration_seconds=2.345,
            elapsed_time=3.456,
            token_usage=None,
            status="success"
        )
        
        assert "tokens" not in result
    
    def test_normal_format(self):
        """Test normal format"""
        formatter = FlowFormatter(detail_level="normal")
        
        result = formatter.format_llm_call(
            model="qwen2.5:7b",
            prompt="What is AI?",
            response="AI is artificial intelligence",
            duration_seconds=2.345,
            elapsed_time=3.456,
            token_usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            status="success"
        )
        
        assert "LLM_CALL" in result
        assert "[+3.456s]" in result
        assert "Model: qwen2.5:7b" in result
        assert "Status: SUCCESS" in result
        assert "Duration: 2.345s" in result
        assert "Tokens: 10 prompt + 20 completion = 30 total" in result
        assert "Prompt:" in result
        assert "What is AI?" in result
        assert "Response:" in result
        assert "AI is artificial intelligence" in result


class TestErrorFormatting:
    """Tests for error entry formatting"""
    
    def test_minimal_format(self):
        """Test minimal format"""
        formatter = FlowFormatter(detail_level="minimal")
        
        result = formatter.format_error(
            error_type="ValueError",
            error_message="Invalid input",
            stack_trace=None,
            elapsed_time=1.234
        )
        
        assert "[+1.234s]" in result
        assert "ERROR" in result
        assert "ValueError" in result
        assert "Invalid input" in result
    
    def test_normal_format_with_stack_trace(self):
        """Test normal format with stack trace"""
        formatter = FlowFormatter(detail_level="normal")
        stack_trace = "Traceback (most recent call last):\n  File 'test.py', line 10"
        
        result = formatter.format_error(
            error_type="ValueError",
            error_message="Invalid input",
            stack_trace=stack_trace,
            elapsed_time=1.234
        )
        
        assert "ERROR" in result
        assert "[+1.234s]" in result
        assert "Error Type: ValueError" in result
        assert "Message: Invalid input" in result
        assert "Stack Trace:" in result
        assert "Traceback" in result
    
    def test_normal_format_without_stack_trace(self):
        """Test normal format without stack trace"""
        formatter = FlowFormatter(detail_level="normal")
        
        result = formatter.format_error(
            error_type="ValueError",
            error_message="Invalid input",
            stack_trace=None,
            elapsed_time=1.234
        )
        
        assert "Stack Trace:" not in result


class TestQueryCompleteFormatting:
    """Tests for query complete entry formatting"""
    
    def test_minimal_format_success(self):
        """Test minimal format for success"""
        formatter = FlowFormatter(detail_level="minimal")
        
        result = formatter.format_query_complete(
            session_id="test-123",
            final_answer="The answer is 42",
            total_duration_seconds=5.678,
            status="success"
        )
        
        assert "[+5.678s]" in result
        assert "COMPLETE" in result
        assert "test-123" in result
        assert "SUCCESS" in result
        assert "[5.678s total]" in result
    
    def test_minimal_format_error(self):
        """Test minimal format for error"""
        formatter = FlowFormatter(detail_level="minimal")
        
        result = formatter.format_query_complete(
            session_id="test-123",
            final_answer="",
            total_duration_seconds=2.345,
            status="error"
        )
        
        assert "ERROR" in result
    
    def test_normal_format_success(self):
        """Test normal format for success"""
        formatter = FlowFormatter(detail_level="normal")
        
        result = formatter.format_query_complete(
            session_id="test-123",
            final_answer="The answer is 42",
            total_duration_seconds=5.678,
            status="success"
        )
        
        assert "QUERY_COMPLETE" in result
        assert "Session: test-123" in result
        assert "[+5.678s]" in result
        assert "Status: SUCCESS" in result
        assert "Total Duration: 5.678s" in result
        assert "Final Answer:" in result
        assert "The answer is 42" in result
    
    def test_normal_format_error_no_answer(self):
        """Test normal format for error without answer"""
        formatter = FlowFormatter(detail_level="normal")
        
        result = formatter.format_query_complete(
            session_id="test-123",
            final_answer="",
            total_duration_seconds=2.345,
            status="error"
        )
        
        assert "Status: ERROR" in result
        assert "Final Answer:" not in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
