"""
Unit tests for LLMCallLogger.

Tests request logging, response logging, error logging, request/response
correlation, and file I/O mocking.
"""

import json
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from rag5.utils.llm_logger import LLMCallLogger


class TestLLMCallLogger:
    """Test suite for LLMCallLogger"""
    
    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        yield log_file
        # Cleanup
        if os.path.exists(log_file):
            os.unlink(log_file)
    
    @pytest.fixture
    def logger_sync(self, temp_log_file):
        """Create a logger with synchronous writing"""
        return LLMCallLogger(
            log_file=temp_log_file,
            async_logging=False
        )
    
    @pytest.fixture
    def logger_with_redaction(self, temp_log_file):
        """Create a logger with redaction enabled"""
        return LLMCallLogger(
            log_file=temp_log_file,
            redact_prompts=True,
            redact_responses=True,
            async_logging=False
        )
    
    @pytest.fixture
    def logger_with_size_limit(self, temp_log_file):
        """Create a logger with size limit"""
        return LLMCallLogger(
            log_file=temp_log_file,
            max_entry_size=1000,
            async_logging=False
        )
    
    def test_initialization_creates_log_directory(self):
        """Test that logger creates log directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "subdir", "test.log")
            logger = LLMCallLogger(log_file=log_file, async_logging=False)
            
            # Directory should be created
            assert os.path.exists(os.path.dirname(log_file))
    
    def test_log_request_basic(self, logger_sync, temp_log_file):
        """Test basic request logging"""
        logger_sync.log_request(
            request_id="req-123",
            session_id="session-456",
            model="qwen2.5:7b",
            prompt="What is the capital of France?",
            config={"temperature": 0.1, "timeout": 120}
        )
        
        # Read and verify log file
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_line = f.readline()
        
        log_entry = json.loads(log_line)
        
        assert log_entry["log_type"] == "llm_request"
        assert log_entry["request_id"] == "req-123"
        assert log_entry["session_id"] == "session-456"
        assert log_entry["model"] == "qwen2.5:7b"
        assert log_entry["prompt"] == "What is the capital of France?"
        assert log_entry["config"]["temperature"] == 0.1
    
    def test_log_request_with_correlation_id(self, logger_sync, temp_log_file):
        """Test request logging with correlation ID"""
        logger_sync.log_request(
            request_id="req-123",
            session_id="session-456",
            model="qwen2.5:7b",
            prompt="Test prompt",
            config={},
            correlation_id="corr-789"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["correlation_id"] == "corr-789"
    
    def test_log_request_with_large_prompt(self, logger_with_size_limit, temp_log_file):
        """Test request logging with large prompt that gets truncated"""
        large_prompt = "A" * 5000
        
        logger_with_size_limit.log_request(
            request_id="req-123",
            session_id="session-456",
            model="qwen2.5:7b",
            prompt=large_prompt,
            config={}
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        # Prompt should be truncated
        assert len(log_entry["prompt"]) < len(large_prompt)
        assert "[TRUNCATED:" in log_entry["prompt"]
    
    def test_log_request_disabled(self, temp_log_file):
        """Test that request logging can be disabled"""
        logger = LLMCallLogger(
            log_file=temp_log_file,
            enable_prompt_logging=False,
            async_logging=False
        )
        
        logger.log_request(
            request_id="req-123",
            session_id="session-456",
            model="qwen2.5:7b",
            prompt="Test prompt",
            config={}
        )
        
        # Log file should be empty
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == ""
    
    def test_log_response_basic(self, logger_sync, temp_log_file):
        """Test basic response logging"""
        logger_sync.log_response(
            request_id="req-123",
            session_id="session-456",
            response="The capital of France is Paris.",
            duration_seconds=2.345
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["log_type"] == "llm_response"
        assert log_entry["request_id"] == "req-123"
        assert log_entry["session_id"] == "session-456"
        assert log_entry["response"] == "The capital of France is Paris."
        assert log_entry["duration_seconds"] == 2.345
        assert log_entry["status"] == "success"
    
    def test_log_response_with_token_usage(self, logger_sync, temp_log_file):
        """Test response logging with token usage"""
        token_usage = {
            "prompt_tokens": 234,
            "completion_tokens": 123,
            "total_tokens": 357
        }
        
        logger_sync.log_response(
            request_id="req-123",
            session_id="session-456",
            response="Test response",
            duration_seconds=1.5,
            token_usage=token_usage
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert "token_usage" in log_entry
        assert log_entry["token_usage"]["prompt_tokens"] == 234
        assert log_entry["token_usage"]["completion_tokens"] == 123
        assert log_entry["token_usage"]["total_tokens"] == 357
    
    def test_log_response_disabled(self, temp_log_file):
        """Test that response logging can be disabled"""
        logger = LLMCallLogger(
            log_file=temp_log_file,
            enable_response_logging=False,
            async_logging=False
        )
        
        logger.log_response(
            request_id="req-123",
            session_id="session-456",
            response="Test response",
            duration_seconds=1.0
        )
        
        # Log file should be empty
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == ""
    
    def test_log_error(self, logger_sync, temp_log_file):
        """Test error logging"""
        error = ValueError("Invalid input")
        
        logger_sync.log_error(
            request_id="req-123",
            session_id="session-456",
            error=error,
            duration_seconds=0.5
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["log_type"] == "llm_response"
        assert log_entry["status"] == "error"
        assert log_entry["request_id"] == "req-123"
        assert log_entry["error_type"] == "ValueError"
        assert log_entry["error_message"] == "Invalid input"
        assert log_entry["duration_seconds"] == 0.5
    
    def test_request_response_correlation(self, logger_sync, temp_log_file):
        """Test that request and response can be correlated via request_id"""
        request_id = "req-123"
        session_id = "session-456"
        
        # Log request
        logger_sync.log_request(
            request_id=request_id,
            session_id=session_id,
            model="qwen2.5:7b",
            prompt="Test prompt",
            config={}
        )
        
        # Log response
        logger_sync.log_response(
            request_id=request_id,
            session_id=session_id,
            response="Test response",
            duration_seconds=1.0
        )
        
        # Read both log entries
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            request_entry = json.loads(f.readline())
            response_entry = json.loads(f.readline())
        
        # Verify correlation
        assert request_entry["request_id"] == response_entry["request_id"]
        assert request_entry["session_id"] == response_entry["session_id"]
        assert request_entry["request_id"] == request_id
    
    def test_redaction_prompts(self, logger_with_redaction, temp_log_file):
        """Test that prompts are redacted when enabled"""
        logger_with_redaction.log_request(
            request_id="req-123",
            session_id="session-456",
            model="qwen2.5:7b",
            prompt="Sensitive information here",
            config={}
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        # Prompt should be redacted
        assert "[REDACTED:" in log_entry["prompt"]
        assert "Sensitive information" not in log_entry["prompt"]
    
    def test_redaction_responses(self, logger_with_redaction, temp_log_file):
        """Test that responses are redacted when enabled"""
        logger_with_redaction.log_response(
            request_id="req-123",
            session_id="session-456",
            response="Sensitive response data",
            duration_seconds=1.0
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        # Response should be redacted
        assert "[REDACTED:" in log_entry["response"]
        assert "Sensitive response" not in log_entry["response"]
    
    def test_error_messages_not_redacted(self, logger_with_redaction, temp_log_file):
        """Test that error messages are never redacted"""
        error = ValueError("Sensitive error information")
        
        logger_with_redaction.log_error(
            request_id="req-123",
            session_id="session-456",
            error=error,
            duration_seconds=0.5
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        # Error message should NOT be redacted
        assert log_entry["error_message"] == "Sensitive error information"
        assert "[REDACTED:" not in log_entry["error_message"]
    
    def test_chinese_characters_preserved(self, logger_sync, temp_log_file):
        """Test that Chinese characters are preserved in logs"""
        logger_sync.log_request(
            request_id="req-123",
            session_id="session-456",
            model="qwen2.5:7b",
            prompt="李小勇是谁？",
            config={}
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["prompt"] == "李小勇是谁？"
    
    def test_logging_failure_does_not_raise(self, logger_sync):
        """Test that logging failures don't break the application"""
        # Mock file writing to raise an exception
        with patch('builtins.open', side_effect=IOError("Disk full")):
            # Should not raise an exception
            logger_sync.log_request(
                request_id="req-123",
                session_id="session-456",
                model="qwen2.5:7b",
                prompt="Test prompt",
                config={}
            )
    
    def test_multiple_requests_in_sequence(self, logger_sync, temp_log_file):
        """Test logging multiple requests in sequence"""
        for i in range(5):
            logger_sync.log_request(
                request_id=f"req-{i}",
                session_id="session-456",
                model="qwen2.5:7b",
                prompt=f"Prompt {i}",
                config={}
            )
        
        # Read all log entries
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 5
        
        # Verify each entry
        for i, line in enumerate(lines):
            log_entry = json.loads(line)
            assert log_entry["request_id"] == f"req-{i}"
            assert log_entry["prompt"] == f"Prompt {i}"
    
    def test_flush_method(self, temp_log_file):
        """Test that flush method works"""
        logger = LLMCallLogger(
            log_file=temp_log_file,
            async_logging=True
        )
        
        logger.log_request(
            request_id="req-123",
            session_id="session-456",
            model="qwen2.5:7b",
            prompt="Test prompt",
            config={}
        )
        
        # Flush should not raise
        logger.flush()
        
        # Cleanup
        logger.shutdown()
    
    def test_shutdown_method(self, temp_log_file):
        """Test that shutdown method works"""
        logger = LLMCallLogger(
            log_file=temp_log_file,
            async_logging=True
        )
        
        logger.log_request(
            request_id="req-123",
            session_id="session-456",
            model="qwen2.5:7b",
            prompt="Test prompt",
            config={}
        )
        
        # Shutdown should not raise
        logger.shutdown(timeout=2.0)
    
    def test_deprecated_redact_sensitive_parameter(self, temp_log_file):
        """Test that deprecated redact_sensitive parameter still works"""
        logger = LLMCallLogger(
            log_file=temp_log_file,
            redact_sensitive=True,
            async_logging=False
        )
        
        # Both prompts and responses should be redacted
        assert logger.redact_prompts is True
        assert logger.redact_responses is True
