"""
Unit tests for FlowLogAnalyzer.

Tests log file parsing, session filtering, timing statistics calculation,
error finding, slow operation finding, and export functionality.
"""

import pytest
import tempfile
import os
import json
import csv
from pathlib import Path
from datetime import datetime

from rag5.utils.flow_analyzer import FlowLogAnalyzer
from rag5.utils.flow_logger import FlowLogger


@pytest.fixture
def sample_log_file():
    """Create a sample log file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_file = f.name
    
    # Create a logger and log some sample entries
    logger = FlowLogger(
        log_file=log_file,
        session_id="session-001",
        async_logging=False
    )
    
    # Log a complete query flow
    logger.log_query_start("What is machine learning?")
    logger.log_query_analysis(
        detected_intent="factual_lookup",
        requires_tools=True,
        reasoning="Query asks for factual information",
        confidence=0.95
    )
    logger.log_tool_selection(
        tool_name="search_knowledge_base",
        rationale="Need to search for ML information",
        confidence=0.90
    )
    logger.log_tool_execution(
        tool_name="search_knowledge_base",
        tool_input="machine learning",
        tool_output="Found 5 documents about ML",
        duration_seconds=0.456,
        status="success"
    )
    logger.log_llm_call(
        model="qwen2.5:7b",
        prompt="Answer based on context",
        response="Machine learning is a branch of AI",
        duration_seconds=2.345,
        token_usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        status="success"
    )
    logger.log_query_complete(
        final_answer="Machine learning is a branch of AI",
        total_duration_seconds=3.0,
        status="success"
    )
    
    # Log another session with an error
    logger2 = FlowLogger(
        log_file=log_file,
        session_id="session-002",
        async_logging=False
    )
    logger2.log_query_start("What is deep learning?")
    logger2.log_error(
        error_type="ConnectionError",
        error_message="Failed to connect to database",
        stack_trace="Traceback..."
    )
    logger2.log_query_complete(
        final_answer="",
        total_duration_seconds=0.5,
        status="error"
    )
    
    # Log a slow operation
    logger3 = FlowLogger(
        log_file=log_file,
        session_id="session-003",
        async_logging=False
    )
    logger3.log_query_start("Complex query")
    logger3.log_tool_execution(
        tool_name="slow_tool",
        tool_input="complex input",
        tool_output="result",
        duration_seconds=6.5,  # Slow operation
        status="success"
    )
    logger3.log_query_complete(
        final_answer="Result",
        total_duration_seconds=7.0,
        status="success"
    )
    
    yield log_file
    
    # Cleanup
    if os.path.exists(log_file):
        os.unlink(log_file)


class TestFlowLogAnalyzerInitialization:
    """Tests for FlowLogAnalyzer initialization"""
    
    def test_initialization_with_existing_file(self, sample_log_file):
        """Test analyzer initialization with existing log file"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        assert analyzer.log_file == sample_log_file
        assert isinstance(analyzer.entries, list)
        assert len(analyzer.entries) > 0
    
    def test_initialization_with_nonexistent_file(self):
        """Test analyzer initialization with non-existent file"""
        analyzer = FlowLogAnalyzer("/path/that/does/not/exist.log")
        
        # Should not raise, just have empty entries
        assert analyzer.entries == []


class TestLogFileParsing:
    """Tests for log file parsing"""
    
    def test_parse_query_start_entry(self, sample_log_file):
        """Test parsing of query start entries"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        query_starts = [e for e in analyzer.entries if e['event_type'] == 'QUERY_START']
        
        assert len(query_starts) >= 1
        assert query_starts[0]['session_id'] is not None
        assert query_starts[0]['timestamp'] is not None
    
    def test_parse_tool_execution_entry(self, sample_log_file):
        """Test parsing of tool execution entries"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        tool_execs = [e for e in analyzer.entries if e['event_type'] in ('TOOL_EXECUTION', 'TOOL_EXEC')]
        
        assert len(tool_execs) >= 1
        assert 'duration' in tool_execs[0]['metadata']
        assert 'status' in tool_execs[0]['metadata']
    
    def test_parse_llm_call_entry(self, sample_log_file):
        """Test parsing of LLM call entries"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        llm_calls = [e for e in analyzer.entries if e['event_type'] == 'LLM_CALL']
        
        assert len(llm_calls) >= 1
        assert 'duration' in llm_calls[0]['metadata']
        assert 'model' in llm_calls[0]['metadata']
    
    def test_parse_error_entry(self, sample_log_file):
        """Test parsing of error entries"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        errors = [e for e in analyzer.entries if e['event_type'] == 'ERROR']
        
        assert len(errors) >= 1
        assert 'error_type' in errors[0]['metadata']
        assert 'error_message' in errors[0]['metadata']
    
    def test_parse_query_complete_entry(self, sample_log_file):
        """Test parsing of query complete entries"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        completes = [e for e in analyzer.entries if e['event_type'] in ('QUERY_COMPLETE', 'COMPLETE')]
        
        assert len(completes) >= 1
        assert 'status' in completes[0]['metadata']


class TestSessionFiltering:
    """Tests for session filtering"""
    
    def test_filter_by_existing_session(self, sample_log_file):
        """Test filtering by existing session ID"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        session_entries = analyzer.filter_by_session("session-001")
        
        assert len(session_entries) > 0
        assert all(e['session_id'] == "session-001" for e in session_entries)
    
    def test_filter_by_nonexistent_session(self, sample_log_file):
        """Test filtering by non-existent session ID"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        session_entries = analyzer.filter_by_session("nonexistent-session")
        
        assert len(session_entries) == 0
    
    def test_filter_returns_all_event_types(self, sample_log_file):
        """Test that filtering returns all event types for a session"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        session_entries = analyzer.filter_by_session("session-001")
        event_types = [e['event_type'] for e in session_entries]
        
        # Should have multiple event types
        assert 'QUERY_START' in event_types
        assert any(t in ('QUERY_COMPLETE', 'COMPLETE') for t in event_types)


class TestTimingStatistics:
    """Tests for timing statistics calculation"""
    
    def test_get_timing_stats_structure(self, sample_log_file):
        """Test timing statistics structure"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        stats = analyzer.get_timing_stats()
        
        assert isinstance(stats, dict)
        # Should have at least one operation type
        assert len(stats) > 0
    
    def test_tool_execution_stats(self, sample_log_file):
        """Test tool execution timing statistics"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        stats = analyzer.get_timing_stats()
        
        if 'tool_execution' in stats:
            tool_stats = stats['tool_execution']
            assert 'count' in tool_stats
            assert 'avg' in tool_stats
            assert 'min' in tool_stats
            assert 'max' in tool_stats
            assert 'p95' in tool_stats
            assert tool_stats['count'] > 0
    
    def test_llm_call_stats(self, sample_log_file):
        """Test LLM call timing statistics"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        stats = analyzer.get_timing_stats()
        
        if 'llm_call' in stats:
            llm_stats = stats['llm_call']
            assert 'count' in llm_stats
            assert 'avg' in llm_stats
            assert llm_stats['count'] > 0
    
    def test_query_complete_stats(self, sample_log_file):
        """Test query completion timing statistics"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        stats = analyzer.get_timing_stats()
        
        if 'query_complete' in stats:
            query_stats = stats['query_complete']
            assert 'count' in query_stats
            assert 'avg' in query_stats
            assert query_stats['count'] > 0
    
    def test_stats_calculations_accuracy(self, sample_log_file):
        """Test that statistics calculations are accurate"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        stats = analyzer.get_timing_stats()
        
        # Verify that min <= avg <= max
        for operation_type, operation_stats in stats.items():
            assert operation_stats['min'] <= operation_stats['avg']
            assert operation_stats['avg'] <= operation_stats['max']
            assert operation_stats['p95'] >= operation_stats['avg']


class TestErrorFinding:
    """Tests for error finding"""
    
    def test_find_errors(self, sample_log_file):
        """Test finding all errors"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        errors = analyzer.find_errors()
        
        assert len(errors) > 0
        assert all('error_type' in e for e in errors)
        assert all('error_message' in e for e in errors)
    
    def test_error_context_included(self, sample_log_file):
        """Test that error context is included"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        errors = analyzer.find_errors()
        
        if errors:
            error = errors[0]
            assert 'timestamp' in error
            assert 'session_id' in error
            assert 'raw_content' in error
    
    def test_find_errors_with_no_errors(self):
        """Test finding errors when there are none"""
        # Create a log file with no errors
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        logger = FlowLogger(
            log_file=log_file,
            session_id="test-session",
            async_logging=False
        )
        logger.log_query_start("Test query")
        logger.log_query_complete("Answer", 1.0, "success")
        
        analyzer = FlowLogAnalyzer(log_file)
        errors = analyzer.find_errors()
        
        assert len(errors) == 0
        
        # Cleanup
        os.unlink(log_file)


class TestSlowOperationFinding:
    """Tests for slow operation finding"""
    
    def test_find_slow_operations_default_threshold(self, sample_log_file):
        """Test finding slow operations with default threshold"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        slow_ops = analyzer.find_slow_operations()
        
        # Should find the 6.5s tool execution and 7.0s query
        assert len(slow_ops) >= 1
        assert all(op['duration'] >= 5.0 for op in slow_ops)
    
    def test_find_slow_operations_custom_threshold(self, sample_log_file):
        """Test finding slow operations with custom threshold"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        slow_ops = analyzer.find_slow_operations(threshold_seconds=2.0)
        
        # Should find more operations with lower threshold
        assert len(slow_ops) > 0
        assert all(op['duration'] >= 2.0 for op in slow_ops)
    
    def test_slow_operation_details(self, sample_log_file):
        """Test that slow operation details are included"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        slow_ops = analyzer.find_slow_operations(threshold_seconds=2.0)
        
        if slow_ops:
            op = slow_ops[0]
            assert 'timestamp' in op
            assert 'session_id' in op
            assert 'event_type' in op
            assert 'operation' in op
            assert 'duration' in op
            assert 'threshold' in op
    
    def test_find_slow_operations_with_none(self):
        """Test finding slow operations when there are none"""
        # Create a log file with only fast operations
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        logger = FlowLogger(
            log_file=log_file,
            session_id="test-session",
            async_logging=False
        )
        logger.log_query_start("Test query")
        logger.log_tool_execution(
            tool_name="fast_tool",
            tool_input="input",
            tool_output="output",
            duration_seconds=0.1,
            status="success"
        )
        logger.log_query_complete("Answer", 0.5, "success")
        
        analyzer = FlowLogAnalyzer(log_file)
        slow_ops = analyzer.find_slow_operations(threshold_seconds=5.0)
        
        assert len(slow_ops) == 0
        
        # Cleanup
        os.unlink(log_file)


class TestJSONExport:
    """Tests for JSON export"""
    
    def test_export_to_json(self, sample_log_file):
        """Test exporting to JSON format"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            output_file = f.name
        
        try:
            analyzer.export_to_json(output_file)
            
            # Verify file was created
            assert os.path.exists(output_file)
            
            # Verify JSON is valid
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert isinstance(data, list)
            assert len(data) > 0
            
            # Verify structure
            entry = data[0]
            assert 'timestamp' in entry
            assert 'event_type' in entry
            assert 'session_id' in entry
            assert 'metadata' in entry
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_export_to_json_creates_directory(self, sample_log_file):
        """Test that export creates output directory if needed"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "subdir", "output.json")
            
            analyzer.export_to_json(output_file)
            
            assert os.path.exists(output_file)


class TestCSVExport:
    """Tests for CSV export"""
    
    def test_export_to_csv(self, sample_log_file):
        """Test exporting to CSV format"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            output_file = f.name
        
        try:
            analyzer.export_to_csv(output_file)
            
            # Verify file was created
            assert os.path.exists(output_file)
            
            # Verify CSV is valid
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            assert len(rows) > 1  # Header + data rows
            
            # Verify header
            header = rows[0]
            assert 'Timestamp' in header
            assert 'Event Type' in header
            assert 'Session ID' in header
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_export_to_csv_creates_directory(self, sample_log_file):
        """Test that export creates output directory if needed"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "subdir", "output.csv")
            
            analyzer.export_to_csv(output_file)
            
            assert os.path.exists(output_file)
    
    def test_csv_content_accuracy(self, sample_log_file):
        """Test that CSV content is accurate"""
        analyzer = FlowLogAnalyzer(sample_log_file)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            output_file = f.name
        
        try:
            analyzer.export_to_csv(output_file)
            
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Verify we have data rows
            assert len(rows) > 0
            
            # Verify row structure
            row = rows[0]
            assert 'Timestamp' in row
            assert 'Event Type' in row
            assert 'Session ID' in row
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestEdgeCases:
    """Tests for edge cases"""
    
    def test_empty_log_file(self):
        """Test analyzer with empty log file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        analyzer = FlowLogAnalyzer(log_file)
        
        assert analyzer.entries == []
        assert analyzer.get_timing_stats() == {}
        assert analyzer.find_errors() == []
        assert analyzer.find_slow_operations() == []
        
        os.unlink(log_file)
    
    def test_malformed_log_entries(self):
        """Test analyzer with malformed log entries"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
            f.write("This is not a valid log entry\n")
            f.write("Neither is this\n")
        
        analyzer = FlowLogAnalyzer(log_file)
        
        # Should handle gracefully without crashing
        assert isinstance(analyzer.entries, list)
        
        os.unlink(log_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
