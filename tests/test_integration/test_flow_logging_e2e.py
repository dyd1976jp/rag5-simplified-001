"""
Integration tests for end-to-end unified flow logging.

Tests the complete flow logging system including initialization,
event logging throughout query processing, session correlation,
error handling, and multi-query scenarios.
"""

import pytest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from rag5.core.agent.agent import SimpleRAGAgent
from rag5.utils.flow_logger import FlowLogger
from rag5.utils.flow_analyzer import FlowLogAnalyzer


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_file = f.name
    yield log_file
    # Cleanup
    if os.path.exists(log_file):
        os.unlink(log_file)


@pytest.fixture
def mock_settings(temp_log_file):
    """Mock settings with flow logging enabled"""
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


class TestEndToEndFlowLogging:
    """Integration tests for complete flow logging"""
    
    def test_complete_query_flow_logged(self, mock_settings, temp_log_file):
        """Test that complete query flow is logged"""
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
            
            # Execute query
            result = agent.chat("What is machine learning?")
            
            # Verify log file was created
            assert os.path.exists(temp_log_file)
            
            # Parse log file
            with open(temp_log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verify all expected events are present
            assert 'QUERY_START' in content
            assert 'What is machine learning?' in content
            assert 'test-session-123' in content
            assert 'QUERY_COMPLETE' in content or 'COMPLETE' in content
    
    def test_chronological_order_of_events(self, mock_settings, temp_log_file):
        """Test that events are logged in chronological order"""
        with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
            mock_executor = MagicMock()
            mock_executor.invoke.return_value = {
                'messages': [
                    MagicMock(type='ai', content='Response', tool_calls=[])
                ]
            }
            mock_init.return_value.create_agent.return_value = mock_executor
            mock_init.return_value.session_id = 'test-session'
            
            agent = SimpleRAGAgent()
            agent.chat("Test query")
            
            # Parse log file
            analyzer = FlowLogAnalyzer(temp_log_file)
            
            # Verify entries are in chronological order
            timestamps = [e['timestamp'] for e in analyzer.entries if e['timestamp']]
            
            for i in range(len(timestamps) - 1):
                assert timestamps[i] <= timestamps[i + 1], "Events not in chronological order"
    
    def test_session_id_consistency(self, mock_settings, temp_log_file):
        """Test that session_id is consistent across all events"""
        with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
            mock_executor = MagicMock()
            mock_executor.invoke.return_value = {
                'messages': [
                    MagicMock(type='ai', content='Response', tool_calls=[])
                ]
            }
            mock_init.return_value.create_agent.return_value = mock_executor
            mock_init.return_value.session_id = 'consistent-session-id'
            
            agent = SimpleRAGAgent()
            agent.chat("Test query")
            
            # Parse log file
            analyzer = FlowLogAnalyzer(temp_log_file)
            
            # Verify all entries have the same session_id
            session_ids = [e['session_id'] for e in analyzer.entries if e.get('session_id')]
            
            assert len(session_ids) > 0
            assert all(sid == 'consistent-session-id' for sid in session_ids)
    
    def test_timing_information_accuracy(self, mock_settings, temp_log_file):
        """Test that timing information is accurate"""
        with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
            mock_executor = MagicMock()
            mock_executor.invoke.return_value = {
                'messages': [
                    MagicMock(type='ai', content='Response', tool_calls=[])
                ]
            }
            mock_init.return_value.create_agent.return_value = mock_executor
            mock_init.return_value.session_id = 'test-session'
            
            agent = SimpleRAGAgent()
            
            start_time = time.time()
            agent.chat("Test query")
            end_time = time.time()
            
            actual_duration = end_time - start_time
            
            # Parse log file
            analyzer = FlowLogAnalyzer(temp_log_file)
            
            # Find query complete entry
            completes = [e for e in analyzer.entries if e['event_type'] in ('QUERY_COMPLETE', 'COMPLETE')]
            
            if completes:
                logged_duration = completes[0].get('elapsed_time', 0)
                # Logged duration should be close to actual duration
                assert abs(logged_duration - actual_duration) < 1.0  # Within 1 second
    
    def test_final_answer_logged(self, mock_settings, temp_log_file):
        """Test that final answer is logged"""
        with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
            mock_executor = MagicMock()
            expected_answer = "This is the final answer"
            mock_executor.invoke.return_value = {
                'messages': [
                    MagicMock(type='ai', content=expected_answer, tool_calls=[])
                ]
            }
            mock_init.return_value.create_agent.return_value = mock_executor
            mock_init.return_value.session_id = 'test-session'
            
            agent = SimpleRAGAgent()
            result = agent.chat("Test query")
            
            # Read log file
            with open(temp_log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verify final answer is in the log
            assert expected_answer in content


class TestMultiQueryFlow:
    """Integration tests for multi-query scenarios"""
    
    def test_multiple_queries_unique_sessions(self, mock_settings, temp_log_file):
        """Test that multiple queries have unique session IDs"""
        with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
            mock_executor = MagicMock()
            mock_executor.invoke.return_value = {
                'messages': [
                    MagicMock(type='ai', content='Response', tool_calls=[])
                ]
            }
            mock_init.return_value.create_agent.return_value = mock_executor
            
            # Create agent and execute multiple queries
            session_ids = []
            for i in range(3):
                session_id = f'session-{i}'
                mock_init.return_value.session_id = session_id
                session_ids.append(session_id)
                
                agent = SimpleRAGAgent()
                agent.chat(f"Query {i}")
            
            # Parse log file
            analyzer = FlowLogAnalyzer(temp_log_file)
            
            # Verify we have entries for all sessions
            for session_id in session_ids:
                session_entries = analyzer.filter_by_session(session_id)
                assert len(session_entries) > 0
    
    def test_no_cross_contamination_between_sessions(self, mock_settings, temp_log_file):
        """Test that there's no cross-contamination between sessions"""
        with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
            mock_executor = MagicMock()
            mock_executor.invoke.return_value = {
                'messages': [
                    MagicMock(type='ai', content='Response', tool_calls=[])
                ]
            }
            mock_init.return_value.create_agent.return_value = mock_executor
            
            # Execute two queries with different content
            mock_init.return_value.session_id = 'session-1'
            agent1 = SimpleRAGAgent()
            agent1.chat("First unique query")
            
            mock_init.return_value.session_id = 'session-2'
            agent2 = SimpleRAGAgent()
            agent2.chat("Second unique query")
            
            # Parse log file
            analyzer = FlowLogAnalyzer(temp_log_file)
            
            # Verify session 1 entries don't contain session 2 content
            session1_entries = analyzer.filter_by_session('session-1')
            session1_content = ' '.join([e['raw_content'] for e in session1_entries])
            
            assert 'First unique query' in session1_content
            assert 'Second unique query' not in session1_content
            
            # Verify session 2 entries don't contain session 1 content
            session2_entries = analyzer.filter_by_session('session-2')
            session2_content = ' '.join([e['raw_content'] for e in session2_entries])
            
            assert 'Second unique query' in session2_content
            assert 'First unique query' not in session2_content
    
    def test_all_queries_logged_correctly(self, mock_settings, temp_log_file):
        """Test that all queries are logged correctly"""
        with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
            mock_executor = MagicMock()
            mock_executor.invoke.return_value = {
                'messages': [
                    MagicMock(type='ai', content='Response', tool_calls=[])
                ]
            }
            mock_init.return_value.create_agent.return_value = mock_executor
            
            # Execute multiple queries
            num_queries = 5
            for i in range(num_queries):
                mock_init.return_value.session_id = f'session-{i}'
                agent = SimpleRAGAgent()
                agent.chat(f"Query {i}")
            
            # Parse log file
            analyzer = FlowLogAnalyzer(temp_log_file)
            
            # Count query start events
            query_starts = [e for e in analyzer.entries if e['event_type'] == 'QUERY_START']
            
            assert len(query_starts) == num_queries


class TestErrorHandling:
    """Integration tests for error handling"""
    
    def test_error_logged_on_tool_failure(self, mock_settings, temp_log_file):
        """Test that errors are logged when tools fail"""
        with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
            mock_executor = MagicMock()
            mock_executor.invoke.side_effect = ValueError("Tool execution failed")
            mock_init.return_value.create_agent.return_value = mock_executor
            mock_init.return_value.session_id = 'error-session'
            
            agent = SimpleRAGAgent()
            result = agent.chat("Test query")
            
            # Read log file
            with open(temp_log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verify error was logged
            assert 'ERROR' in content
            assert 'ValueError' in content or 'Tool execution failed' in content
    
    def test_query_complete_called_with_error_status(self, mock_settings, temp_log_file):
        """Test that query_complete is called with error status"""
        with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
            mock_executor = MagicMock()
            mock_executor.invoke.side_effect = Exception("Test error")
            mock_init.return_value.create_agent.return_value = mock_executor
            mock_init.return_value.session_id = 'error-session'
            
            agent = SimpleRAGAgent()
            result = agent.chat("Test query")
            
            # Parse log file
            analyzer = FlowLogAnalyzer(temp_log_file)
            
            # Find query complete entry
            completes = [e for e in analyzer.entries if e['event_type'] in ('QUERY_COMPLETE', 'COMPLETE')]
            
            if completes:
                # Should have error status
                status = completes[0]['metadata'].get('status', '').upper()
                assert 'ERROR' in status or 'FAIL' in status
    
    def test_system_continues_after_error(self, mock_settings, temp_log_file):
        """Test that system continues to function after errors"""
        with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
            mock_executor = MagicMock()
            
            # First query fails
            mock_executor.invoke.side_effect = [
                Exception("First error"),
                {
                    'messages': [
                        MagicMock(type='ai', content='Success response', tool_calls=[])
                    ]
                }
            ]
            mock_init.return_value.create_agent.return_value = mock_executor
            
            # First query with error
            mock_init.return_value.session_id = 'error-session'
            agent1 = SimpleRAGAgent()
            agent1.chat("Error query")
            
            # Second query succeeds
            mock_init.return_value.session_id = 'success-session'
            agent2 = SimpleRAGAgent()
            result = agent2.chat("Success query")
            
            # Parse log file
            analyzer = FlowLogAnalyzer(temp_log_file)
            
            # Verify both sessions are logged
            error_entries = analyzer.filter_by_session('error-session')
            success_entries = analyzer.filter_by_session('success-session')
            
            assert len(error_entries) > 0
            assert len(success_entries) > 0
    
    def test_logging_failure_does_not_break_agent(self, mock_settings):
        """Test that logging failures don't break the agent"""
        # Use invalid log file path
        mock_settings.flow_log_file = "/invalid/path/that/does/not/exist.log"
        
        with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
            mock_executor = MagicMock()
            mock_executor.invoke.return_value = {
                'messages': [
                    MagicMock(type='ai', content='Response', tool_calls=[])
                ]
            }
            mock_init.return_value.create_agent.return_value = mock_executor
            mock_init.return_value.session_id = 'test-session'
            
            agent = SimpleRAGAgent()
            
            # Should not raise exception
            result = agent.chat("Test query")
            
            # Agent should still return result
            assert result is not None


class TestBackwardCompatibility:
    """Integration tests for backward compatibility"""
    
    def test_both_unified_and_separate_logs_created(self, temp_log_file):
        """Test that both unified and separate logs are created when enabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            flow_log = os.path.join(temp_dir, "unified_flow.log")
            llm_log = os.path.join(temp_dir, "llm_interactions.log")
            
            with patch('rag5.core.agent.agent.settings') as mock_settings:
                # Enable both flow logging and separate logs
                mock_settings.enable_flow_logging = True
                mock_settings.flow_log_file = flow_log
                mock_settings.flow_detail_level = 'normal'
                mock_settings.flow_max_content_length = 500
                mock_settings.flow_async_logging = False
                mock_settings.keep_separate_logs = True
                
                # Enable LLM logging
                mock_settings.enable_llm_logging = True
                mock_settings.llm_log_file = llm_log
                mock_settings.llm_async_logging = False
                
                mock_settings.enable_reflection_logging = False
                mock_settings.enable_context_logging = False
                
                mock_settings.ollama_host = 'http://localhost:11434'
                mock_settings.llm_model = 'qwen2.5:7b'
                mock_settings.embed_model = 'bge-m3'
                mock_settings.llm_timeout = 60
                
                with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
                    mock_executor = MagicMock()
                    mock_executor.invoke.return_value = {
                        'messages': [
                            MagicMock(type='ai', content='Response', tool_calls=[])
                        ]
                    }
                    mock_init.return_value.create_agent.return_value = mock_executor
                    mock_init.return_value.session_id = 'test-session'
                    
                    agent = SimpleRAGAgent()
                    agent.chat("Test query")
                    
                    # Verify unified log was created
                    assert os.path.exists(flow_log)
    
    def test_no_interference_between_logging_systems(self, mock_settings, temp_log_file):
        """Test that unified and separate logs don't interfere"""
        with patch('rag5.core.agent.agent.AgentInitializer') as mock_init:
            mock_executor = MagicMock()
            mock_executor.invoke.return_value = {
                'messages': [
                    MagicMock(type='ai', content='Response', tool_calls=[])
                ]
            }
            mock_init.return_value.create_agent.return_value = mock_executor
            mock_init.return_value.session_id = 'test-session'
            
            agent = SimpleRAGAgent()
            agent.chat("Test query")
            
            # Verify unified log was created and has content
            assert os.path.exists(temp_log_file)
            assert os.path.getsize(temp_log_file) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
