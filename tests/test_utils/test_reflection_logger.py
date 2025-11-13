"""
Unit tests for AgentReflectionLogger.

Tests each reflection type (query_analysis, tool_decision, query_reformulation,
retrieval_evaluation, synthesis_decision), JSON formatting, file writing,
and session_id/correlation_id tracking.
"""

import json
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from rag5.utils.reflection_logger import AgentReflectionLogger


class TestAgentReflectionLogger:
    """Test suite for AgentReflectionLogger"""
    
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
        return AgentReflectionLogger(
            log_file=temp_log_file,
            session_id="test-session-123",
            async_logging=False
        )
    
    @pytest.fixture
    def logger_with_size_limit(self, temp_log_file):
        """Create a logger with size limit"""
        return AgentReflectionLogger(
            log_file=temp_log_file,
            session_id="test-session-123",
            max_entry_size=1000,
            async_logging=False
        )
    
    def test_initialization_creates_log_directory(self):
        """Test that logger creates log directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "subdir", "reflections.log")
            logger = AgentReflectionLogger(
                log_file=log_file,
                async_logging=False
            )
            
            # Directory should be created
            assert os.path.exists(os.path.dirname(log_file))
    
    def test_initialization_generates_session_id(self, temp_log_file):
        """Test that logger generates session_id if not provided"""
        logger = AgentReflectionLogger(
            log_file=temp_log_file,
            async_logging=False
        )
        
        # Session ID should be generated
        assert logger.session_id is not None
        assert logger.session_id.startswith("session-")
    
    def test_initialization_uses_provided_session_id(self, temp_log_file):
        """Test that logger uses provided session_id"""
        logger = AgentReflectionLogger(
            log_file=temp_log_file,
            session_id="custom-session-456",
            async_logging=False
        )
        
        assert logger.session_id == "custom-session-456"
    
    def test_log_query_analysis_basic(self, logger_sync, temp_log_file):
        """Test basic query analysis logging"""
        logger_sync.log_query_analysis(
            original_query="李小勇和人合作入股了什么公司",
            detected_intent="factual_lookup",
            requires_tools=True,
            reasoning="Query contains specific entity names and asks for factual information"
        )
        
        # Read and verify log file
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_line = f.readline()
        
        log_entry = json.loads(log_line)
        
        assert log_entry["log_type"] == "agent_reflection"
        assert log_entry["session_id"] == "test-session-123"
        assert log_entry["reflection_type"] == "query_analysis"
        assert log_entry["data"]["original_query"] == "李小勇和人合作入股了什么公司"
        assert log_entry["data"]["detected_intent"] == "factual_lookup"
        assert log_entry["data"]["requires_tools"] is True
        assert "Query contains specific entity names" in log_entry["data"]["reasoning"]
    
    def test_log_query_analysis_with_confidence(self, logger_sync, temp_log_file):
        """Test query analysis logging with confidence score"""
        logger_sync.log_query_analysis(
            original_query="What is the weather?",
            detected_intent="conversational",
            requires_tools=False,
            reasoning="Simple conversational query",
            confidence=0.95
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert "confidence" in log_entry["data"]
        assert log_entry["data"]["confidence"] == 0.95
    
    def test_log_query_analysis_with_correlation_id(self, logger_sync, temp_log_file):
        """Test query analysis logging with correlation ID"""
        logger_sync.log_query_analysis(
            original_query="Test query",
            detected_intent="test",
            requires_tools=True,
            reasoning="Test reasoning",
            correlation_id="corr-789"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["correlation_id"] == "corr-789"
    
    def test_log_tool_decision_basic(self, logger_sync, temp_log_file):
        """Test basic tool decision logging"""
        logger_sync.log_tool_decision(
            tool_name="search_knowledge_base",
            decision_rationale="Need to search for factual information about entities",
            confidence=0.92
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["log_type"] == "agent_reflection"
        assert log_entry["reflection_type"] == "tool_decision"
        assert log_entry["data"]["tool_name"] == "search_knowledge_base"
        assert "factual information" in log_entry["data"]["decision_rationale"]
        assert log_entry["data"]["confidence"] == 0.92
    
    def test_log_tool_decision_with_query_context(self, logger_sync, temp_log_file):
        """Test tool decision logging with query context"""
        logger_sync.log_tool_decision(
            tool_name="search_knowledge_base",
            decision_rationale="Query requires knowledge base lookup",
            confidence=0.88,
            query_context="User asked about specific company information"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert "query_context" in log_entry["data"]
        assert "company information" in log_entry["data"]["query_context"]
    
    def test_log_tool_decision_with_correlation_id(self, logger_sync, temp_log_file):
        """Test tool decision logging with correlation ID"""
        logger_sync.log_tool_decision(
            tool_name="search_knowledge_base",
            decision_rationale="Test rationale",
            confidence=0.9,
            correlation_id="corr-456"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["correlation_id"] == "corr-456"
    
    def test_log_query_reformulation_basic(self, logger_sync, temp_log_file):
        """Test basic query reformulation logging"""
        logger_sync.log_query_reformulation(
            original_query="李小勇的公司",
            reformulated_query="李小勇 AND (公司 OR 企业 OR 入股)",
            reasoning="Expanded query with synonyms and boolean operators for better recall"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["log_type"] == "agent_reflection"
        assert log_entry["reflection_type"] == "query_reformulation"
        assert log_entry["data"]["original_query"] == "李小勇的公司"
        assert "AND" in log_entry["data"]["reformulated_query"]
        assert "synonyms" in log_entry["data"]["reasoning"]
    
    def test_log_query_reformulation_with_correlation_id(self, logger_sync, temp_log_file):
        """Test query reformulation logging with correlation ID"""
        logger_sync.log_query_reformulation(
            original_query="original",
            reformulated_query="reformulated",
            reasoning="test reasoning",
            correlation_id="corr-123"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["correlation_id"] == "corr-123"
    
    def test_log_retrieval_evaluation_basic(self, logger_sync, temp_log_file):
        """Test basic retrieval evaluation logging"""
        logger_sync.log_retrieval_evaluation(
            query="李小勇和人合作入股了什么公司",
            results_count=5,
            top_scores=[0.92, 0.87, 0.81, 0.76, 0.65],
            relevance_assessment="High relevance: top 3 results contain direct information about the query"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["log_type"] == "agent_reflection"
        assert log_entry["reflection_type"] == "retrieval_evaluation"
        assert log_entry["data"]["query"] == "李小勇和人合作入股了什么公司"
        assert log_entry["data"]["results_count"] == 5
        assert len(log_entry["data"]["top_scores"]) == 5
        assert log_entry["data"]["top_scores"][0] == 0.92
        assert "High relevance" in log_entry["data"]["relevance_assessment"]
    
    def test_log_retrieval_evaluation_rounds_scores(self, logger_sync, temp_log_file):
        """Test that retrieval evaluation rounds scores to 3 decimal places"""
        logger_sync.log_retrieval_evaluation(
            query="test",
            results_count=2,
            top_scores=[0.123456789, 0.987654321],
            relevance_assessment="test"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        # Scores should be rounded to 3 decimal places
        assert log_entry["data"]["top_scores"][0] == 0.123
        assert log_entry["data"]["top_scores"][1] == 0.988
    
    def test_log_retrieval_evaluation_with_correlation_id(self, logger_sync, temp_log_file):
        """Test retrieval evaluation logging with correlation ID"""
        logger_sync.log_retrieval_evaluation(
            query="test",
            results_count=1,
            top_scores=[0.9],
            relevance_assessment="test",
            correlation_id="corr-999"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["correlation_id"] == "corr-999"
    
    def test_log_synthesis_decision_basic(self, logger_sync, temp_log_file):
        """Test basic synthesis decision logging"""
        logger_sync.log_synthesis_decision(
            sources_used=3,
            confidence=0.89,
            reasoning="Sufficient information from multiple sources to provide comprehensive answer"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["log_type"] == "agent_reflection"
        assert log_entry["reflection_type"] == "synthesis_decision"
        assert log_entry["data"]["sources_used"] == 3
        assert log_entry["data"]["confidence"] == 0.89
        assert "Sufficient information" in log_entry["data"]["reasoning"]
    
    def test_log_synthesis_decision_with_sufficient_info_flag(self, logger_sync, temp_log_file):
        """Test synthesis decision logging with has_sufficient_info flag"""
        logger_sync.log_synthesis_decision(
            sources_used=1,
            confidence=0.45,
            reasoning="Limited information available",
            has_sufficient_info=False
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert "has_sufficient_info" in log_entry["data"]
        assert log_entry["data"]["has_sufficient_info"] is False
    
    def test_log_synthesis_decision_with_correlation_id(self, logger_sync, temp_log_file):
        """Test synthesis decision logging with correlation ID"""
        logger_sync.log_synthesis_decision(
            sources_used=2,
            confidence=0.8,
            reasoning="test",
            correlation_id="corr-111"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["correlation_id"] == "corr-111"
    
    def test_json_formatting_valid(self, logger_sync, temp_log_file):
        """Test that all log entries produce valid JSON"""
        # Log various reflection types
        logger_sync.log_query_analysis(
            original_query="test",
            detected_intent="test",
            requires_tools=True,
            reasoning="test"
        )
        
        logger_sync.log_tool_decision(
            tool_name="test_tool",
            decision_rationale="test",
            confidence=0.9
        )
        
        logger_sync.log_retrieval_evaluation(
            query="test",
            results_count=1,
            top_scores=[0.9],
            relevance_assessment="test"
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
            assert "reflection_type" in log_entry
            assert "data" in log_entry
    
    def test_session_id_tracking_consistent(self, logger_sync, temp_log_file):
        """Test that session_id is consistent across multiple log entries"""
        # Log multiple reflections
        logger_sync.log_query_analysis(
            original_query="query1",
            detected_intent="test",
            requires_tools=True,
            reasoning="test"
        )
        
        logger_sync.log_tool_decision(
            tool_name="tool1",
            decision_rationale="test",
            confidence=0.9
        )
        
        logger_sync.log_synthesis_decision(
            sources_used=1,
            confidence=0.8,
            reasoning="test"
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
        logger_sync.log_query_analysis(
            original_query="test",
            detected_intent="test",
            requires_tools=True,
            reasoning="test",
            correlation_id=correlation_id
        )
        
        logger_sync.log_tool_decision(
            tool_name="test_tool",
            decision_rationale="test",
            confidence=0.9,
            correlation_id=correlation_id
        )
        
        logger_sync.log_retrieval_evaluation(
            query="test",
            results_count=1,
            top_scores=[0.9],
            relevance_assessment="test",
            correlation_id=correlation_id
        )
        
        # Read all entries
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # All should have the same correlation_id
        correlation_ids = [json.loads(line)["correlation_id"] for line in lines]
        assert len(set(correlation_ids)) == 1
        assert correlation_ids[0] == correlation_id
    
    def test_large_reasoning_text_truncated(self, logger_with_size_limit, temp_log_file):
        """Test that large reasoning text is truncated"""
        large_reasoning = "A" * 5000
        
        logger_with_size_limit.log_query_analysis(
            original_query="test",
            detected_intent="test",
            requires_tools=True,
            reasoning=large_reasoning
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        # Reasoning should be truncated
        assert len(log_entry["data"]["reasoning"]) < len(large_reasoning)
        assert "[TRUNCATED:" in log_entry["data"]["reasoning"]
    
    def test_chinese_characters_preserved(self, logger_sync, temp_log_file):
        """Test that Chinese characters are preserved in logs"""
        logger_sync.log_query_analysis(
            original_query="李小勇和人合作入股了什么公司",
            detected_intent="事实查询",
            requires_tools=True,
            reasoning="查询包含特定实体名称并询问事实信息"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["data"]["original_query"] == "李小勇和人合作入股了什么公司"
        assert log_entry["data"]["detected_intent"] == "事实查询"
        assert "特定实体名称" in log_entry["data"]["reasoning"]
    
    def test_logging_failure_does_not_raise(self, logger_sync):
        """Test that logging failures don't break the application"""
        # Mock file writing to raise an exception
        with patch('builtins.open', side_effect=IOError("Disk full")):
            # Should not raise an exception
            logger_sync.log_query_analysis(
                original_query="test",
                detected_intent="test",
                requires_tools=True,
                reasoning="test"
            )
    
    def test_multiple_reflections_in_sequence(self, logger_sync, temp_log_file):
        """Test logging multiple reflections in sequence"""
        for i in range(5):
            logger_sync.log_query_analysis(
                original_query=f"query {i}",
                detected_intent="test",
                requires_tools=True,
                reasoning=f"reasoning {i}"
            )
        
        # Read all log entries
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 5
        
        # Verify each entry
        for i, line in enumerate(lines):
            log_entry = json.loads(line)
            assert log_entry["data"]["original_query"] == f"query {i}"
            assert log_entry["data"]["reasoning"] == f"reasoning {i}"
    
    def test_confidence_rounded_to_three_decimals(self, logger_sync, temp_log_file):
        """Test that confidence scores are rounded to 3 decimal places"""
        logger_sync.log_tool_decision(
            tool_name="test_tool",
            decision_rationale="test",
            confidence=0.123456789
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry["data"]["confidence"] == 0.123
    
    def test_flush_method(self, temp_log_file):
        """Test that flush method works"""
        logger = AgentReflectionLogger(
            log_file=temp_log_file,
            async_logging=True
        )
        
        logger.log_query_analysis(
            original_query="test",
            detected_intent="test",
            requires_tools=True,
            reasoning="test"
        )
        
        # Flush should not raise
        logger.flush()
        
        # Cleanup
        logger.shutdown()
    
    def test_shutdown_method(self, temp_log_file):
        """Test that shutdown method works"""
        logger = AgentReflectionLogger(
            log_file=temp_log_file,
            async_logging=True
        )
        
        logger.log_query_analysis(
            original_query="test",
            detected_intent="test",
            requires_tools=True,
            reasoning="test"
        )
        
        # Shutdown should not raise
        logger.shutdown(timeout=2.0)
    
    def test_timestamp_format(self, logger_sync, temp_log_file):
        """Test that timestamp is in correct ISO format"""
        logger_sync.log_query_analysis(
            original_query="test",
            detected_intent="test",
            requires_tools=True,
            reasoning="test"
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        # Timestamp should be in ISO format
        timestamp = log_entry["timestamp"]
        assert "T" in timestamp
        assert "Z" in timestamp or "+" in timestamp or "-" in timestamp
    
    def test_all_reflection_types_have_correct_structure(self, logger_sync, temp_log_file):
        """Test that all reflection types have the correct log structure"""
        # Log one of each type
        logger_sync.log_query_analysis(
            original_query="test",
            detected_intent="test",
            requires_tools=True,
            reasoning="test"
        )
        
        logger_sync.log_tool_decision(
            tool_name="test_tool",
            decision_rationale="test",
            confidence=0.9
        )
        
        logger_sync.log_query_reformulation(
            original_query="original",
            reformulated_query="reformulated",
            reasoning="test"
        )
        
        logger_sync.log_retrieval_evaluation(
            query="test",
            results_count=1,
            top_scores=[0.9],
            relevance_assessment="test"
        )
        
        logger_sync.log_synthesis_decision(
            sources_used=1,
            confidence=0.8,
            reasoning="test"
        )
        
        # Read all entries
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 5
        
        # Verify structure of each entry
        for line in lines:
            log_entry = json.loads(line)
            
            # All should have these fields
            assert log_entry["log_type"] == "agent_reflection"
            assert "timestamp" in log_entry
            assert "session_id" in log_entry
            assert "reflection_type" in log_entry
            assert "data" in log_entry
            
            # reflection_type should be one of the expected types
            assert log_entry["reflection_type"] in [
                "query_analysis",
                "tool_decision",
                "query_reformulation",
                "retrieval_evaluation",
                "synthesis_decision"
            ]
