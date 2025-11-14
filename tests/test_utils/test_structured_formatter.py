"""
Unit tests for StructuredLogFormatter.

Tests JSON formatting for different log types, timestamp formatting,
field validation, and JSON parseability.
"""

import json
import pytest
from datetime import datetime
from rag5.utils.structured_formatter import StructuredLogFormatter


class TestStructuredLogFormatter:
    """Test suite for StructuredLogFormatter"""
    
    @pytest.fixture
    def formatter(self):
        """Create a formatter instance"""
        return StructuredLogFormatter()
    
    @pytest.fixture
    def formatter_with_size_limit(self):
        """Create a formatter with size limit"""
        return StructuredLogFormatter(max_entry_size=1000)
    
    def test_timestamp_format(self, formatter):
        """Test timestamp formatting with millisecond precision"""
        timestamp = formatter._get_timestamp()
        
        # Verify format: YYYY-MM-DDTHH:MM:SS.fffZ
        assert timestamp.endswith('Z')
        assert 'T' in timestamp
        assert '.' in timestamp
        
        # Verify it's parseable
        # Remove 'Z' and parse
        dt = datetime.strptime(timestamp[:-1], "%Y-%m-%dT%H:%M:%S.%f")
        assert isinstance(dt, datetime)
    
    def test_format_llm_request_basic(self, formatter):
        """Test basic LLM request formatting"""
        log_json = formatter.format_llm_request(
            request_id="req-123",
            session_id="session-456",
            model="qwen2.5:7b",
            prompt="What is the capital of France?",
            config={"temperature": 0.1, "timeout": 120}
        )
        
        # Verify JSON is parseable
        log_entry = json.loads(log_json)
        
        # Verify required fields
        assert log_entry["log_type"] == "llm_request"
        assert log_entry["request_id"] == "req-123"
        assert log_entry["session_id"] == "session-456"
        assert log_entry["model"] == "qwen2.5:7b"
        assert log_entry["prompt"] == "What is the capital of France?"
        assert log_entry["prompt_length"] == len("What is the capital of France?")
        assert log_entry["config"]["temperature"] == 0.1
        assert log_entry["config"]["timeout"] == 120
        assert "timestamp" in log_entry
        assert "correlation_id" in log_entry
    
    def test_format_llm_request_with_correlation_id(self, formatter):
        """Test LLM request with explicit correlation ID"""
        log_json = formatter.format_llm_request(
            request_id="req-123",
            session_id="session-456",
            model="qwen2.5:7b",
            prompt="Test prompt",
            config={},
            correlation_id="corr-789"
        )
        
        log_entry = json.loads(log_json)
        assert log_entry["correlation_id"] == "corr-789"
    
    def test_format_llm_request_with_custom_timestamp(self, formatter):
        """Test LLM request with custom timestamp"""
        custom_timestamp = "2025-11-09T21:04:01.123Z"
        log_json = formatter.format_llm_request(
            request_id="req-123",
            session_id="session-456",
            model="qwen2.5:7b",
            prompt="Test prompt",
            config={},
            timestamp=custom_timestamp
        )
        
        log_entry = json.loads(log_json)
        assert log_entry["timestamp"] == custom_timestamp
    
    def test_format_llm_response_basic(self, formatter):
        """Test basic LLM response formatting"""
        log_json = formatter.format_llm_response(
            request_id="req-123",
            session_id="session-456",
            response="The capital of France is Paris.",
            duration_seconds=2.345
        )
        
        log_entry = json.loads(log_json)
        
        assert log_entry["log_type"] == "llm_response"
        assert log_entry["request_id"] == "req-123"
        assert log_entry["session_id"] == "session-456"
        assert log_entry["response"] == "The capital of France is Paris."
        assert log_entry["response_length"] == len("The capital of France is Paris.")
        assert log_entry["duration_seconds"] == 2.345
        assert log_entry["status"] == "success"
        assert "timestamp" in log_entry
    
    def test_format_llm_response_with_token_usage(self, formatter):
        """Test LLM response with token usage statistics"""
        token_usage = {
            "prompt_tokens": 234,
            "completion_tokens": 123,
            "total_tokens": 357
        }
        
        log_json = formatter.format_llm_response(
            request_id="req-123",
            session_id="session-456",
            response="Test response",
            duration_seconds=1.5,
            token_usage=token_usage
        )
        
        log_entry = json.loads(log_json)
        assert "token_usage" in log_entry
        assert log_entry["token_usage"]["prompt_tokens"] == 234
        assert log_entry["token_usage"]["completion_tokens"] == 123
        assert log_entry["token_usage"]["total_tokens"] == 357
    
    def test_format_llm_response_duration_rounding(self, formatter):
        """Test that duration is rounded to 3 decimal places"""
        log_json = formatter.format_llm_response(
            request_id="req-123",
            session_id="session-456",
            response="Test",
            duration_seconds=2.3456789
        )
        
        log_entry = json.loads(log_json)
        assert log_entry["duration_seconds"] == 2.346
    
    def test_format_llm_error(self, formatter):
        """Test LLM error formatting"""
        log_json = formatter.format_llm_error(
            request_id="req-123",
            session_id="session-456",
            error_message="Connection timeout",
            error_type="TimeoutError",
            duration_seconds=30.0
        )
        
        log_entry = json.loads(log_json)
        
        assert log_entry["log_type"] == "llm_response"
        assert log_entry["status"] == "error"
        assert log_entry["request_id"] == "req-123"
        assert log_entry["error_message"] == "Connection timeout"
        assert log_entry["error_type"] == "TimeoutError"
        assert log_entry["duration_seconds"] == 30.0
    
    def test_format_reflection_query_analysis(self, formatter):
        """Test agent reflection formatting for query analysis"""
        data = {
            "original_query": "李小勇和人合作入股了什么公司",
            "detected_intent": "factual_lookup",
            "requires_tools": True,
            "reasoning": "Query contains specific entity names",
            "confidence": 0.95
        }
        
        log_json = formatter.format_reflection(
            session_id="session-456",
            reflection_type="query_analysis",
            data=data
        )
        
        log_entry = json.loads(log_json)
        
        assert log_entry["log_type"] == "agent_reflection"
        assert log_entry["session_id"] == "session-456"
        assert log_entry["reflection_type"] == "query_analysis"
        assert log_entry["data"]["original_query"] == "李小勇和人合作入股了什么公司"
        assert log_entry["data"]["detected_intent"] == "factual_lookup"
        assert log_entry["data"]["requires_tools"] is True
        assert log_entry["data"]["confidence"] == 0.95
    
    def test_format_reflection_tool_decision(self, formatter):
        """Test agent reflection formatting for tool decision"""
        data = {
            "tool_name": "search_knowledge_base",
            "decision_rationale": "Need to search for entity information",
            "confidence": 0.9
        }
        
        log_json = formatter.format_reflection(
            session_id="session-456",
            reflection_type="tool_decision",
            data=data
        )
        
        log_entry = json.loads(log_json)
        assert log_entry["reflection_type"] == "tool_decision"
        assert log_entry["data"]["tool_name"] == "search_knowledge_base"
    
    def test_format_context_event_message_added(self, formatter):
        """Test conversation context event formatting for message addition"""
        data = {
            "role": "user",
            "content_length": 45,
            "total_messages": 3,
            "total_tokens": 150
        }
        
        log_json = formatter.format_context_event(
            session_id="session-456",
            event_type="message_added",
            data=data
        )
        
        log_entry = json.loads(log_json)
        
        assert log_entry["log_type"] == "conversation_context"
        assert log_entry["session_id"] == "session-456"
        assert log_entry["event_type"] == "message_added"
        assert log_entry["data"]["role"] == "user"
        assert log_entry["data"]["total_messages"] == 3
    
    def test_format_context_event_truncation(self, formatter):
        """Test conversation context event formatting for truncation"""
        data = {
            "strategy": "sliding_window",
            "messages_removed": 2,
            "tokens_saved": 500
        }
        
        log_json = formatter.format_context_event(
            session_id="session-456",
            event_type="context_truncation",
            data=data
        )
        
        log_entry = json.loads(log_json)
        assert log_entry["event_type"] == "context_truncation"
        assert log_entry["data"]["messages_removed"] == 2
    
    def test_format_context_event_reset(self, formatter):
        """Test conversation context event formatting for reset"""
        data = {
            "trigger": "user_request",
            "final_size": 0
        }
        
        log_json = formatter.format_context_event(
            session_id="session-456",
            event_type="context_reset",
            data=data
        )
        
        log_entry = json.loads(log_json)
        assert log_entry["event_type"] == "context_reset"
        assert log_entry["data"]["trigger"] == "user_request"
    
    def test_json_with_chinese_characters(self, formatter):
        """Test that Chinese characters are preserved in JSON"""
        log_json = formatter.format_llm_request(
            request_id="req-123",
            session_id="session-456",
            model="qwen2.5:7b",
            prompt="李小勇是谁？",
            config={}
        )
        
        log_entry = json.loads(log_json)
        assert log_entry["prompt"] == "李小勇是谁？"
        # Verify Chinese characters are not escaped
        assert "李小勇" in log_json
    
    def test_truncate_if_needed_no_limit(self, formatter):
        """Test truncation when no size limit is set"""
        long_text = "A" * 10000
        result = formatter.truncate_if_needed(long_text)
        assert result == long_text
    
    def test_truncate_if_needed_within_limit(self, formatter_with_size_limit):
        """Test truncation when text is within limit"""
        short_text = "This is a short text"
        result = formatter_with_size_limit.truncate_if_needed(short_text)
        assert result == short_text
    
    def test_truncate_if_needed_exceeds_limit(self, formatter_with_size_limit):
        """Test truncation when text exceeds limit"""
        long_text = "A" * 2000
        result = formatter_with_size_limit.truncate_if_needed(long_text)
        
        # Should be truncated
        assert len(result) < len(long_text)
        assert "[TRUNCATED:" in result
        assert "bytes]" in result
    
    def test_truncate_preserves_context(self, formatter_with_size_limit):
        """Test that truncation preserves first and last characters"""
        # Create text with distinctive start and end
        long_text = "START" + ("X" * 2000) + "END"
        result = formatter_with_size_limit.truncate_if_needed(long_text, preserve_chars=10)
        
        # Should contain start and end
        assert "START" in result
        assert "END" in result
        assert "[TRUNCATED:" in result
    
    def test_all_log_types_have_required_fields(self, formatter):
        """Test that all log types include required base fields"""
        # Test LLM request
        llm_req = json.loads(formatter.format_llm_request(
            "req-1", "sess-1", "model", "prompt", {}
        ))
        assert "log_type" in llm_req
        assert "timestamp" in llm_req
        assert "session_id" in llm_req
        
        # Test LLM response
        llm_resp = json.loads(formatter.format_llm_response(
            "req-1", "sess-1", "response", 1.0
        ))
        assert "log_type" in llm_resp
        assert "timestamp" in llm_resp
        assert "session_id" in llm_resp
        
        # Test reflection
        reflection = json.loads(formatter.format_reflection(
            "sess-1", "query_analysis", {}
        ))
        assert "log_type" in reflection
        assert "timestamp" in reflection
        assert "session_id" in reflection
        
        # Test context event
        context = json.loads(formatter.format_context_event(
            "sess-1", "message_added", {}
        ))
        assert "log_type" in context
        assert "timestamp" in context
        assert "session_id" in context
    
    def test_correlation_id_defaults_to_request_id(self, formatter):
        """Test that correlation_id defaults to request_id for LLM logs"""
        log_json = formatter.format_llm_request(
            request_id="req-123",
            session_id="session-456",
            model="model",
            prompt="prompt",
            config={}
        )
        
        log_entry = json.loads(log_json)
        assert log_entry["correlation_id"] == "req-123"
    
    def test_correlation_id_defaults_to_session_id(self, formatter):
        """Test that correlation_id defaults to session_id for reflection/context logs"""
        # Test reflection
        reflection_json = formatter.format_reflection(
            session_id="session-456",
            reflection_type="query_analysis",
            data={}
        )
        reflection = json.loads(reflection_json)
        assert reflection["correlation_id"] == "session-456"
        
        # Test context event
        context_json = formatter.format_context_event(
            session_id="session-456",
            event_type="message_added",
            data={}
        )
        context = json.loads(context_json)
        assert context["correlation_id"] == "session-456"
