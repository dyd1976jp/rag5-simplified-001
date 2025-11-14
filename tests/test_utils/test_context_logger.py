"""
Unit tests for ConversationContextLogger.

Tests message addition logging, context truncation logging, context reset logging,
and message count tracking.
"""

import json
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from rag5.utils.context_logger import ConversationContextLogger


class TestConversationContextLogger:
    """Test suite for ConversationContextLogger"""
    
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
        return ConversationContextLogger(
            log_file=temp_log_file,
            session_id="test-session-123",
            async_logging=False
        )
    
    def test_initialization_creates_log_directory(self):
        """Test that logger creates log directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "subdir", "context.log")
            logger = ConversationContextLogger(
                log_file=log_file,
                async_logging=False
            )
            
            # Directory should be created
            assert os.path.exists(os.path.dirname(log_file))
    
    def test_initialization_generates_session_id(self, temp_log_file):
        """Test that logger generates session_id if not provided"""
        logger = ConversationContextLogger(
            log_file=temp_log_file,
            async_logging=False
        )
        
        # Session ID should be generated (UUID format)
        assert logger.session_id is not None
        assert len(logger.session_id) == 36  # UUID format: 8-4-4-4-12
        assert logger.session_id.count('-') == 4
    
    def test_initialization_uses_provided_session_id(self, temp_log_file):
        """Test that logger uses provided session_id"""
        logger = ConversationContextLogger(
            log_file=temp_log_file,
            session_id="custom-session-456",
            async_logging=False
        )
        
        assert logger.session_id == "custom-session-456"
    
    def test_log_message_added_basic(self, logger_sync, temp_log_file):
        """Test basic message addition logging"""
        logger_sync.log_message_added(
            role="user",
            content_length=45,
            total_messages=3,
            total_tokens=150
        )
        
        # Read and verify log file
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_line = f.readline()
        
        log_entry = json.loads(log_line)
        
        assert log_entry["log_type"] == "conversation_context"
        assert log_entry["session_id"] == "test-session-123"
        assert log_entry["event_type"] == "message_added"
        assert log_entry["data"]["role"] == "user"
        assert log_entry["data"]["content_length"] == 45
        assert log_entry["data"]["total_messages"] == 3
        assert log_entry["data"]["total_tokens"] == 150
    
    def test_log_message_added_assistant_role(self, logger_sync, temp_log_file):
        """Test message addition logging for assistant role"""
        logger_sync.log_message_added(
            role="assistant",
            content_length=120,
            total_messages=4,
            total_tokens=300
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["data"]["role"] == "assistant"
        assert log_entry["data"]["content_length"] == 120
    
    def test_log_message_added_system_role(self, logger_sync, temp_log_file):
        """Test message addition logging for system role"""
        logger_sync.log_message_added(
            role="system",
            content_length=200,
            total_messages=1,
            total_tokens=50
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["data"]["role"] == "system"
    
    def test_log_message_added_with_correlation_id(self, logger_sync, temp_log_file):
        """Test message addition logging with correlation ID"""
        logger_sync.log_message_added(
            role="user",
            content_length=50,
            total_messages=2,
            total_tokens=100,
            correlation_id="corr-789"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["correlation_id"] == "corr-789"
    
    def test_log_context_truncation_basic(self, logger_sync, temp_log_file):
        """Test basic context truncation logging"""
        logger_sync.log_context_truncation(
            strategy="oldest_first",
            messages_removed=2,
            tokens_saved=100
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["log_type"] == "conversation_context"
        assert log_entry["event_type"] == "context_truncation"
        assert log_entry["data"]["strategy"] == "oldest_first"
        assert log_entry["data"]["messages_removed"] == 2
        assert log_entry["data"]["tokens_saved"] == 100
    
    def test_log_context_truncation_sliding_window(self, logger_sync, temp_log_file):
        """Test context truncation logging with sliding window strategy"""
        logger_sync.log_context_truncation(
            strategy="sliding_window",
            messages_removed=5,
            tokens_saved=250
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["data"]["strategy"] == "sliding_window"
        assert log_entry["data"]["messages_removed"] == 5
        assert log_entry["data"]["tokens_saved"] == 250
    
    def test_log_context_truncation_with_correlation_id(self, logger_sync, temp_log_file):
        """Test context truncation logging with correlation ID"""
        logger_sync.log_context_truncation(
            strategy="oldest_first",
            messages_removed=1,
            tokens_saved=50,
            correlation_id="corr-456"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["correlation_id"] == "corr-456"
    
    def test_log_context_reset_basic(self, logger_sync, temp_log_file):
        """Test basic context reset logging"""
        logger_sync.log_context_reset(
            trigger="user_request",
            final_size=0
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["log_type"] == "conversation_context"
        assert log_entry["event_type"] == "context_reset"
        assert log_entry["data"]["trigger"] == "user_request"
        assert log_entry["data"]["final_size"] == 0
    
    def test_log_context_reset_max_length_trigger(self, logger_sync, temp_log_file):
        """Test context reset logging with max_length trigger"""
        logger_sync.log_context_reset(
            trigger="max_length",
            final_size=1
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["data"]["trigger"] == "max_length"
        assert log_entry["data"]["final_size"] == 1
    
    def test_log_context_reset_new_session_trigger(self, logger_sync, temp_log_file):
        """Test context reset logging with new_session trigger"""
        logger_sync.log_context_reset(
            trigger="new_session",
            final_size=0
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["data"]["trigger"] == "new_session"
    
    def test_log_context_reset_with_correlation_id(self, logger_sync, temp_log_file):
        """Test context reset logging with correlation ID"""
        logger_sync.log_context_reset(
            trigger="user_request",
            final_size=0,
            correlation_id="corr-123"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["correlation_id"] == "corr-123"
    
    def test_json_formatting_valid(self, logger_sync, temp_log_file):
        """Test that all log entries produce valid JSON"""
        # Log various event types
        logger_sync.log_message_added(
            role="user",
            content_length=50,
            total_messages=1,
            total_tokens=25
        )
        
        logger_sync.log_context_truncation(
            strategy="oldest_first",
            messages_removed=2,
            tokens_saved=100
        )
        
        logger_sync.log_context_reset(
            trigger="user_request",
            final_size=0
        )
        
        # Read and parse all entries
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        
        # All should be valid JSON
        for line in lines:
            log_entry = json.loads(line)  # Should not raise
            assert "log_type" in log_entry
            assert "timestamp" in log_entry
            assert "session_id" in log_entry
            assert "event_type" in log_entry
            assert "data" in log_entry
    
    def test_session_id_tracking_consistent(self, logger_sync, temp_log_file):
        """Test that session_id is consistent across multiple log entries"""
        # Log multiple events
        logger_sync.log_message_added(
            role="user",
            content_length=50,
            total_messages=1,
            total_tokens=25
        )
        
        logger_sync.log_message_added(
            role="assistant",
            content_length=100,
            total_messages=2,
            total_tokens=75
        )
        
        logger_sync.log_context_truncation(
            strategy="oldest_first",
            messages_removed=1,
            tokens_saved=50
        )
        
        # Read all entries
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # All should have the same session_id
        session_ids = [json.loads(line)["session_id"] for line in lines]
        assert len(set(session_ids)) == 1
        assert session_ids[0] == "test-session-123"
    
    def test_correlation_id_tracking(self, logger_sync, temp_log_file):
        """Test that correlation_id links related operations"""
        correlation_id = "operation-xyz"
        
        # Log related operations with same correlation_id
        logger_sync.log_message_added(
            role="user",
            content_length=50,
            total_messages=1,
            total_tokens=25,
            correlation_id=correlation_id
        )
        
        logger_sync.log_message_added(
            role="assistant",
            content_length=100,
            total_messages=2,
            total_tokens=75,
            correlation_id=correlation_id
        )
        
        logger_sync.log_context_truncation(
            strategy="oldest_first",
            messages_removed=1,
            tokens_saved=50,
            correlation_id=correlation_id
        )
        
        # Read all entries
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # All should have the same correlation_id
        correlation_ids = [json.loads(line)["correlation_id"] for line in lines]
        assert len(set(correlation_ids)) == 1
        assert correlation_ids[0] == correlation_id
    
    def test_message_count_tracking(self, logger_sync, temp_log_file):
        """Test that message count is tracked correctly"""
        # Simulate adding messages to context
        logger_sync.log_message_added(
            role="user",
            content_length=50,
            total_messages=1,
            total_tokens=25
        )
        
        logger_sync.log_message_added(
            role="assistant",
            content_length=100,
            total_messages=2,
            total_tokens=75
        )
        
        logger_sync.log_message_added(
            role="user",
            content_length=60,
            total_messages=3,
            total_tokens=135
        )
        
        # Read all entries
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Verify message count increases
        counts = [json.loads(line)["data"]["total_messages"] for line in lines]
        assert counts == [1, 2, 3]
    
    def test_token_count_tracking(self, logger_sync, temp_log_file):
        """Test that token count is tracked correctly"""
        # Simulate adding messages with token tracking
        logger_sync.log_message_added(
            role="user",
            content_length=50,
            total_messages=1,
            total_tokens=25
        )
        
        logger_sync.log_message_added(
            role="assistant",
            content_length=100,
            total_messages=2,
            total_tokens=75
        )
        
        # Read all entries
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Verify token count increases
        tokens = [json.loads(line)["data"]["total_tokens"] for line in lines]
        assert tokens == [25, 75]
    
    def test_logging_failure_does_not_raise(self, logger_sync):
        """Test that logging failures don't break the application"""
        # Mock file writing to raise an exception
        with patch('builtins.open', side_effect=IOError("Disk full")):
            # Should not raise an exception
            logger_sync.log_message_added(
                role="user",
                content_length=50,
                total_messages=1,
                total_tokens=25
            )
    
    def test_multiple_events_in_sequence(self, logger_sync, temp_log_file):
        """Test logging multiple events in sequence"""
        for i in range(5):
            logger_sync.log_message_added(
                role="user" if i % 2 == 0 else "assistant",
                content_length=50 + i * 10,
                total_messages=i + 1,
                total_tokens=25 + i * 15
            )
        
        # Read all log entries
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 5
        
        # Verify each entry
        for i, line in enumerate(lines):
            log_entry = json.loads(line)
            assert log_entry["data"]["total_messages"] == i + 1
            assert log_entry["data"]["content_length"] == 50 + i * 10
    
    def test_flush_method(self, temp_log_file):
        """Test that flush method works"""
        logger = ConversationContextLogger(
            log_file=temp_log_file,
            async_logging=True
        )
        
        logger.log_message_added(
            role="user",
            content_length=50,
            total_messages=1,
            total_tokens=25
        )
        
        # Flush should not raise
        logger.flush()
        
        # Cleanup
        logger.shutdown()
    
    def test_shutdown_method(self, temp_log_file):
        """Test that shutdown method works"""
        logger = ConversationContextLogger(
            log_file=temp_log_file,
            async_logging=True
        )
        
        logger.log_message_added(
            role="user",
            content_length=50,
            total_messages=1,
            total_tokens=25
        )
        
        # Shutdown should not raise
        logger.shutdown(timeout=2.0)
    
    def test_timestamp_format(self, logger_sync, temp_log_file):
        """Test that timestamp is in correct ISO format"""
        logger_sync.log_message_added(
            role="user",
            content_length=50,
            total_messages=1,
            total_tokens=25
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        # Timestamp should be in ISO format
        timestamp = log_entry["timestamp"]
        assert "T" in timestamp
        assert "Z" in timestamp or "+" in timestamp or "-" in timestamp
    
    def test_all_event_types_have_correct_structure(self, logger_sync, temp_log_file):
        """Test that all event types have the correct log structure"""
        # Log one of each type
        logger_sync.log_message_added(
            role="user",
            content_length=50,
            total_messages=1,
            total_tokens=25
        )
        
        logger_sync.log_context_truncation(
            strategy="oldest_first",
            messages_removed=2,
            tokens_saved=100
        )
        
        logger_sync.log_context_reset(
            trigger="user_request",
            final_size=0
        )
        
        # Read all entries
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        
        # Verify structure of each entry
        for line in lines:
            log_entry = json.loads(line)
            
            # All should have these fields
            assert log_entry["log_type"] == "conversation_context"
            assert "timestamp" in log_entry
            assert "session_id" in log_entry
            assert "event_type" in log_entry
            assert "data" in log_entry
            
            # event_type should be one of the expected types
            assert log_entry["event_type"] in [
                "message_added",
                "context_truncation",
                "context_reset"
            ]
    
    def test_conversation_flow_simulation(self, logger_sync, temp_log_file):
        """Test simulating a complete conversation flow"""
        # User message
        logger_sync.log_message_added(
            role="user",
            content_length=50,
            total_messages=1,
            total_tokens=25
        )
        
        # Assistant response
        logger_sync.log_message_added(
            role="assistant",
            content_length=150,
            total_messages=2,
            total_tokens=100
        )
        
        # Another user message
        logger_sync.log_message_added(
            role="user",
            content_length=60,
            total_messages=3,
            total_tokens=160
        )
        
        # Context truncation due to length
        logger_sync.log_context_truncation(
            strategy="oldest_first",
            messages_removed=1,
            tokens_saved=25
        )
        
        # Assistant response
        logger_sync.log_message_added(
            role="assistant",
            content_length=120,
            total_messages=3,
            total_tokens=195
        )
        
        # User resets conversation
        logger_sync.log_context_reset(
            trigger="user_request",
            final_size=0
        )
        
        # Read all entries
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 6
        
        # Verify the flow
        entries = [json.loads(line) for line in lines]
        assert entries[0]["event_type"] == "message_added"
        assert entries[1]["event_type"] == "message_added"
        assert entries[2]["event_type"] == "message_added"
        assert entries[3]["event_type"] == "context_truncation"
        assert entries[4]["event_type"] == "message_added"
        assert entries[5]["event_type"] == "context_reset"
    
    def test_large_content_length_values(self, logger_sync, temp_log_file):
        """Test logging with large content length values"""
        logger_sync.log_message_added(
            role="user",
            content_length=10000,
            total_messages=1,
            total_tokens=2500
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["data"]["content_length"] == 10000
        assert log_entry["data"]["total_tokens"] == 2500
    
    def test_zero_values(self, logger_sync, temp_log_file):
        """Test logging with zero values"""
        logger_sync.log_context_reset(
            trigger="new_session",
            final_size=0
        )
        
        logger_sync.log_context_truncation(
            strategy="oldest_first",
            messages_removed=0,
            tokens_saved=0
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        
        reset_entry = json.loads(lines[0])
        assert reset_entry["data"]["final_size"] == 0
        
        truncation_entry = json.loads(lines[1])
        assert truncation_entry["data"]["messages_removed"] == 0
        assert truncation_entry["data"]["tokens_saved"] == 0
