"""
Tests for FlowLogger integration with SimpleRAGAgent.

This module tests that the FlowLogger is properly integrated into the agent
and logs events during query processing.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from rag5.core.agent.agent import SimpleRAGAgent
from rag5.utils.flow_logger import FlowLogger


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_file = f.name
    yield log_file
    # Cleanup
    if os.path.exists(log_file):
        os.unlink(log_file)


@pytest.fixture
def mock_settings(temp_log_file):
    """Mock settings with flow logging enabled."""
    with patch('rag5.core.agent.agent.settings') as mock_settings:
        # Enable flow logging
        mock_settings.enable_flow_logging = True
        mock_settings.flow_log_file = temp_log_file
        mock_settings.flow_detail_level = 'normal'
        mock_settings.flow_max_content_length = 500
        mock_settings.flow_async_logging = False  # Disable async for testing
        
        # Disable other logging to simplify test
        mock_settings.enable_reflection_logging = False
        mock_settings.enable_context_logging = False
        mock_settings.enable_llm_logging = False
        
        # Other required settings
        mock_settings.ollama_host = 'http://localhost:11434'
        mock_settings.llm_model = 'qwen2.5:7b'
        mock_settings.embed_model = 'bge-m3'
        mock_settings.llm_timeout = 60
        
        yield mock_settings


def test_flow_logger_initialization(mock_settings):
    """Test that FlowLogger is properly initialized in the agent."""
    with patch('rag5.core.agent.agent.AgentInitializer'):
        agent = SimpleRAGAgent()
        
        # Verify flow logger is initialized
        assert agent.flow_logger is not None
        assert isinstance(agent.flow_logger, FlowLogger)
        assert agent.flow_logger.enabled is True
        assert agent.flow_logger.detail_level == 'normal'


def test_flow_logger_disabled(temp_log_file):
    """Test that FlowLogger is not initialized when disabled."""
    with patch('rag5.core.agent.agent.settings') as mock_settings:
        mock_settings.enable_flow_logging = False
        mock_settings.enable_reflection_logging = False
        mock_settings.enable_context_logging = False
        mock_settings.enable_llm_logging = False
        
        with patch('rag5.core.agent.agent.AgentInitializer'):
            agent = SimpleRAGAgent()
            
            # Verify flow logger is not initialized
            assert agent.flow_logger is None


def test_flow_logger_query_start_logged(mock_settings, temp_log_file):
    """Test that query start is logged."""
    with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
        # Mock the agent executor
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {
            'messages': [
                MagicMock(type='ai', content='Test response')
            ]
        }
        mock_init.return_value.create_agent.return_value = mock_executor
        mock_init.return_value.session_id = 'test-session-123'
        
        agent = SimpleRAGAgent()
        
        # Call chat method
        try:
            agent.chat("Test query")
        except Exception:
            pass  # Ignore errors, we just want to check logging
        
        # Read log file
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Verify query start was logged
        assert 'QUERY_START' in log_content
        assert 'Test query' in log_content
        assert 'test-session-123' in log_content


def test_flow_logger_query_complete_logged(mock_settings, temp_log_file):
    """Test that query completion is logged."""
    with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
        # Mock the agent executor
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {
            'messages': [
                MagicMock(type='ai', content='Test response', tool_calls=[])
            ]
        }
        mock_init.return_value.create_agent.return_value = mock_executor
        mock_init.return_value.session_id = 'test-session-123'
        
        agent = SimpleRAGAgent()
        
        # Call chat method
        try:
            result = agent.chat("Test query")
        except Exception:
            pass
        
        # Read log file
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Verify query complete was logged
        assert 'QUERY_COMPLETE' in log_content or 'COMPLETE' in log_content


def test_flow_logger_error_logged(mock_settings, temp_log_file):
    """Test that errors are logged."""
    with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
        # Mock the agent executor to raise an error
        mock_executor = MagicMock()
        mock_executor.invoke.side_effect = ValueError("Test error")
        mock_init.return_value.create_agent.return_value = mock_executor
        mock_init.return_value.session_id = 'test-session-123'
        
        agent = SimpleRAGAgent()
        
        # Call chat method (should handle error gracefully)
        result = agent.chat("Test query")
        
        # Read log file
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Verify error was logged
        assert 'ERROR' in log_content
        assert 'ValueError' in log_content or 'Test error' in log_content


def test_flow_logger_shutdown(mock_settings):
    """Test that FlowLogger is properly shut down."""
    with patch('rag5.core.agent.agent.AgentInitializer'):
        agent = SimpleRAGAgent()
        
        # Mock the flush method
        agent.flow_logger.flush = Mock()
        
        # Shutdown agent
        agent.shutdown()
        
        # Verify flush was called
        agent.flow_logger.flush.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
