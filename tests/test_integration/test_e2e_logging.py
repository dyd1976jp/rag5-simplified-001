"""
Integration tests for end-to-end logging functionality.

Tests the complete logging system including LLM interactions, agent reflections,
and conversation context tracking across a real agent execution.
"""

import json
import pytest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch


class TestE2ELogging:
    """Integration tests for end-to-end logging"""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for log files"""
        temp_dir = tempfile.mkdtemp(prefix="rag5_logging_test_")
        yield temp_dir
        # Cleanup
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def log_files(self, temp_log_dir):
        """Return paths to expected log files"""
        return {
            "llm_interactions": os.path.join(temp_log_dir, "llm_interactions.log"),
            "agent_reflections": os.path.join(temp_log_dir, "agent_reflections.log"),
            "conversation_context": os.path.join(temp_log_dir, "conversation_context.log"),
        }
    
    def test_logging_initialization(self, temp_log_dir, log_files):
        """Test that logging components can be initialized"""
        from rag5.utils.llm_logger import LLMCallLogger
        from rag5.utils.reflection_logger import AgentReflectionLogger
        from rag5.utils.context_logger import ConversationContextLogger
        
        # Initialize loggers
        llm_logger = LLMCallLogger(
            log_file=log_files["llm_interactions"],
            async_logging=False
        )
        
        reflection_logger = AgentReflectionLogger(
            log_file=log_files["agent_reflections"],
            async_logging=False
        )
        
        context_logger = ConversationContextLogger(
            log_file=log_files["conversation_context"],
            async_logging=False
        )
        
        # Verify loggers are initialized
        assert llm_logger is not None
        assert reflection_logger is not None
        assert context_logger is not None
        
        # Verify session IDs are generated for loggers that have them
        assert reflection_logger.session_id is not None
        assert context_logger.session_id is not None
    
    def test_llm_interaction_logging(self, temp_log_dir, log_files):
        """Test LLM interaction logging"""
        from rag5.utils.llm_logger import LLMCallLogger
        from rag5.utils.id_generator import generate_request_id
        
        logger = LLMCallLogger(
            log_file=log_files["llm_interactions"],
            async_logging=False
        )
        
        request_id = generate_request_id()
        session_id = "test-session-123"
        
        # Log a request
        logger.log_request(
            request_id=request_id,
            session_id=session_id,
            model="qwen2.5:7b",
            prompt="What is machine learning?",
            config={"temperature": 0.7, "max_tokens": 500}
        )
        
        # Log a response
        logger.log_response(
            request_id=request_id,
            session_id=session_id,
            response="Machine learning is a branch of AI...",
            duration_seconds=1.5005,
            token_usage={"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60}
        )
        
        # Verify log file exists
        assert os.path.exists(log_files["llm_interactions"])
        
        # Parse and verify log entries
        with open(log_files["llm_interactions"], 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        
        # Verify request log
        request_log = json.loads(lines[0])
        assert request_log["log_type"] == "llm_request"
        assert request_log["session_id"] == "test-session-123"
        assert request_log["request_id"] == request_id
        assert request_log["model"] == "qwen2.5:7b"
        assert "prompt" in request_log
        
        # Verify response log
        response_log = json.loads(lines[1])
        assert response_log["log_type"] == "llm_response"
        assert response_log["session_id"] == "test-session-123"
        assert response_log["request_id"] == request_id
        assert response_log["token_usage"]["prompt_tokens"] == 10
        assert response_log["token_usage"]["completion_tokens"] == 50
        assert response_log["token_usage"]["total_tokens"] == 60
    
    def test_agent_reflection_logging(self, temp_log_dir, log_files):
        """Test agent reflection logging"""
        from rag5.utils.reflection_logger import AgentReflectionLogger
        
        logger = AgentReflectionLogger(
            log_file=log_files["agent_reflections"],
            session_id="test-session-123",
            async_logging=False
        )
        
        correlation_id = "query-abc123"
        
        # Log query analysis
        logger.log_query_analysis(
            original_query="What is machine learning?",
            detected_intent="factual_lookup",
            requires_tools=True,
            reasoning="Query asks for factual information",
            correlation_id=correlation_id
        )
        
        # Log tool decision
        logger.log_tool_decision(
            tool_name="search_knowledge_base",
            decision_rationale="Need to search for ML information",
            confidence=0.95,
            correlation_id=correlation_id
        )
        
        # Log retrieval evaluation
        logger.log_retrieval_evaluation(
            query="machine learning",
            results_count=5,
            top_scores=[0.92, 0.87, 0.81, 0.76, 0.65],
            relevance_assessment="High relevance results",
            correlation_id=correlation_id
        )
        
        # Verify log file exists
        assert os.path.exists(log_files["agent_reflections"])
        
        # Parse and verify log entries
        with open(log_files["agent_reflections"], 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        
        # Verify all entries have same correlation_id
        for line in lines:
            log_entry = json.loads(line)
            assert log_entry["log_type"] == "agent_reflection"
            assert log_entry["session_id"] == "test-session-123"
            assert log_entry["correlation_id"] == correlation_id
    
    def test_conversation_context_logging(self, temp_log_dir, log_files):
        """Test conversation context logging"""
        from rag5.utils.context_logger import ConversationContextLogger
        
        logger = ConversationContextLogger(
            log_file=log_files["conversation_context"],
            session_id="test-session-123",
            async_logging=False
        )
        
        # Log message additions
        logger.log_message_added(
            role="user",
            content_length=50,
            total_messages=1,
            total_tokens=25
        )
        
        logger.log_message_added(
            role="assistant",
            content_length=150,
            total_messages=2,
            total_tokens=100
        )
        
        # Log context truncation
        logger.log_context_truncation(
            strategy="oldest_first",
            messages_removed=1,
            tokens_saved=25
        )
        
        # Verify log file exists
        assert os.path.exists(log_files["conversation_context"])
        
        # Parse and verify log entries
        with open(log_files["conversation_context"], 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        
        # Verify entries
        for line in lines:
            log_entry = json.loads(line)
            assert log_entry["log_type"] == "conversation_context"
            assert log_entry["session_id"] == "test-session-123"
    
    def test_request_response_correlation(self, temp_log_dir, log_files):
        """Test that request and response are correlated via request_id"""
        from rag5.utils.llm_logger import LLMCallLogger
        from rag5.utils.id_generator import generate_request_id
        
        logger = LLMCallLogger(
            log_file=log_files["llm_interactions"],
            async_logging=False
        )
        
        session_id = "test-session-123"
        
        # Create multiple request-response pairs
        for i in range(3):
            request_id = generate_request_id()
            
            logger.log_request(
                request_id=request_id,
                session_id=session_id,
                model="qwen2.5:7b",
                prompt=f"Query {i}",
                config={"temperature": 0.7}
            )
            
            logger.log_response(
                request_id=request_id,
                session_id=session_id,
                response=f"Response {i}",
                duration_seconds=1.0,
                token_usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
            )
        
        # Parse logs
        with open(log_files["llm_interactions"], 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 6  # 3 requests + 3 responses
        
        # Verify correlation
        for i in range(0, 6, 2):
            request_log = json.loads(lines[i])
            response_log = json.loads(lines[i + 1])
            
            # Same request_id
            assert request_log["request_id"] == response_log["request_id"]
            
            # Same session_id
            assert request_log["session_id"] == response_log["session_id"]
    
    def test_session_id_consistency(self, temp_log_dir, log_files):
        """Test that session_id is consistent across all logs"""
        from rag5.utils.llm_logger import LLMCallLogger
        from rag5.utils.reflection_logger import AgentReflectionLogger
        from rag5.utils.context_logger import ConversationContextLogger
        
        session_id = "test-session-456"
        
        # Initialize all loggers with same session_id
        llm_logger = LLMCallLogger(
            log_file=log_files["llm_interactions"],
            async_logging=False
        )
        
        reflection_logger = AgentReflectionLogger(
            log_file=log_files["agent_reflections"],
            session_id=session_id,
            async_logging=False
        )
        
        context_logger = ConversationContextLogger(
            log_file=log_files["conversation_context"],
            session_id=session_id,
            async_logging=False
        )
        
        # Log to each logger
        llm_logger.log_request(
            request_id="req-1",
            session_id=session_id,
            model="qwen2.5:7b",
            prompt="Test",
            config={"temperature": 0.7}
        )
        
        reflection_logger.log_query_analysis(
            original_query="Test",
            detected_intent="test",
            requires_tools=False,
            reasoning="Test"
        )
        
        context_logger.log_message_added(
            role="user",
            content_length=10,
            total_messages=1,
            total_tokens=5
        )
        
        # Verify session_id consistency
        all_logs = []
        for log_file in log_files.values():
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        all_logs.append(json.loads(line))
        
        # All logs should have the same session_id
        for log_entry in all_logs:
            assert log_entry["session_id"] == session_id
    
    def test_timing_information_accuracy(self, temp_log_dir, log_files):
        """Test that timing information is accurate"""
        from rag5.utils.llm_logger import LLMCallLogger
        
        logger = LLMCallLogger(
            log_file=log_files["llm_interactions"],
            async_logging=False
        )
        
        # Log response with specific duration
        logger.log_response(
            request_id="req-1",
            session_id="test-session",
            response="Test response",
            duration_seconds=1.23456,
            token_usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )
        
        # Parse log
        with open(log_files["llm_interactions"], 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        # Verify duration is recorded (rounded to 3 decimal places)
        assert abs(log_entry["duration_seconds"] - 1.235) < 0.001
        
        # Verify timestamp is present and in ISO format
        assert "timestamp" in log_entry
        assert "T" in log_entry["timestamp"]
    
    def test_json_structure_validity(self, temp_log_dir, log_files):
        """Test that all log files contain valid JSON"""
        from rag5.utils.llm_logger import LLMCallLogger
        from rag5.utils.reflection_logger import AgentReflectionLogger
        from rag5.utils.context_logger import ConversationContextLogger
        
        # Create loggers and log some entries
        llm_logger = LLMCallLogger(
            log_file=log_files["llm_interactions"],
            async_logging=False
        )
        llm_logger.log_request(
            request_id="req-1",
            session_id="test-session",
            model="qwen2.5:7b",
            prompt="Test",
            config={"temperature": 0.7}
        )
        
        reflection_logger = AgentReflectionLogger(
            log_file=log_files["agent_reflections"],
            async_logging=False
        )
        reflection_logger.log_query_analysis(
            original_query="Test",
            detected_intent="test",
            requires_tools=False,
            reasoning="Test"
        )
        
        context_logger = ConversationContextLogger(
            log_file=log_files["conversation_context"],
            async_logging=False
        )
        context_logger.log_message_added(
            role="user",
            content_length=10,
            total_messages=1,
            total_tokens=5
        )
        
        # Verify all log files contain valid JSON
        for log_file in log_files.values():
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        # Should not raise
                        log_entry = json.loads(line)
                        
                        # Verify required fields
                        assert "timestamp" in log_entry
                        assert "log_type" in log_entry
                        assert "session_id" in log_entry


class TestMultiTurnConversation:
    """Integration tests for multi-turn conversation logging"""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for log files"""
        temp_dir = tempfile.mkdtemp(prefix="rag5_multiturn_test_")
        yield temp_dir
        # Cleanup
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def log_files(self, temp_log_dir):
        """Return paths to expected log files"""
        return {
            "llm_interactions": os.path.join(temp_log_dir, "llm_interactions.log"),
            "conversation_context": os.path.join(temp_log_dir, "conversation_context.log"),
        }
    
    def test_multi_turn_session_consistency(self, temp_log_dir, log_files):
        """Test that session_id remains consistent across multiple turns"""
        from rag5.utils.llm_logger import LLMCallLogger
        from rag5.utils.context_logger import ConversationContextLogger
        from rag5.utils.id_generator import generate_request_id
        
        session_id = "multi-turn-session-789"
        
        llm_logger = LLMCallLogger(
            log_file=log_files["llm_interactions"],
            async_logging=False
        )
        
        context_logger = ConversationContextLogger(
            log_file=log_files["conversation_context"],
            session_id=session_id,
            async_logging=False
        )
        
        # Simulate 3-turn conversation
        for turn in range(3):
            # User message
            context_logger.log_message_added(
                role="user",
                content_length=50 + turn * 10,
                total_messages=turn * 2 + 1,
                total_tokens=25 + turn * 15
            )
            
            # LLM request/response
            request_id = generate_request_id()
            llm_logger.log_request(
                request_id=request_id,
                session_id=session_id,
                model="qwen2.5:7b",
                prompt=f"Turn {turn} query",
                config={"temperature": 0.7}
            )
            llm_logger.log_response(
                request_id=request_id,
                session_id=session_id,
                response=f"Turn {turn} response",
                duration_seconds=1.0,
                token_usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
            )
            
            # Assistant message
            context_logger.log_message_added(
                role="assistant",
                content_length=100 + turn * 20,
                total_messages=turn * 2 + 2,
                total_tokens=75 + turn * 25
            )
        
        # Verify session_id consistency
        all_logs = []
        for log_file in log_files.values():
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    all_logs.append(json.loads(line))
        
        # All logs should have the same session_id
        for log_entry in all_logs:
            assert log_entry["session_id"] == session_id
    
    def test_context_tracking_across_turns(self, temp_log_dir, log_files):
        """Test that context logging tracks message additions across turns"""
        from rag5.utils.context_logger import ConversationContextLogger
        
        logger = ConversationContextLogger(
            log_file=log_files["conversation_context"],
            session_id="context-test-session",
            async_logging=False
        )
        
        # Simulate conversation with increasing message count
        expected_counts = []
        for turn in range(5):
            # User message
            logger.log_message_added(
                role="user",
                content_length=50,
                total_messages=turn * 2 + 1,
                total_tokens=100 + turn * 50
            )
            expected_counts.append(turn * 2 + 1)
            
            # Assistant message
            logger.log_message_added(
                role="assistant",
                content_length=100,
                total_messages=turn * 2 + 2,
                total_tokens=150 + turn * 50
            )
            expected_counts.append(turn * 2 + 2)
        
        # Parse logs
        with open(log_files["conversation_context"], 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Verify message count progression
        for i, line in enumerate(lines):
            log_entry = json.loads(line)
            assert log_entry["data"]["total_messages"] == expected_counts[i]
    
    def test_conversation_history_in_logs(self, temp_log_dir, log_files):
        """Test that conversation history is reflected in logs"""
        from rag5.utils.context_logger import ConversationContextLogger
        
        logger = ConversationContextLogger(
            log_file=log_files["conversation_context"],
            session_id="history-test-session",
            async_logging=False
        )
        
        # Build up conversation history
        conversation = [
            ("user", 50, 1, 25),
            ("assistant", 100, 2, 75),
            ("user", 60, 3, 135),
            ("assistant", 120, 4, 195),
        ]
        
        for role, content_length, total_messages, total_tokens in conversation:
            logger.log_message_added(
                role=role,
                content_length=content_length,
                total_messages=total_messages,
                total_tokens=total_tokens
            )
        
        # Parse logs
        with open(log_files["conversation_context"], 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 4
        
        # Verify conversation progression
        for i, line in enumerate(lines):
            log_entry = json.loads(line)
            expected_role, expected_length, expected_msgs, expected_tokens = conversation[i]
            
            assert log_entry["data"]["role"] == expected_role
            assert log_entry["data"]["content_length"] == expected_length
            assert log_entry["data"]["total_messages"] == expected_msgs
            assert log_entry["data"]["total_tokens"] == expected_tokens
