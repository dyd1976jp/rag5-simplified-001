"""
Manual test for FlowLogAnalyzer.

This script creates a sample log file and tests the analyzer functionality.
"""

from datetime import datetime
from pathlib import Path
from rag5.utils.flow_analyzer import FlowLogAnalyzer
from rag5.utils.flow_formatter import FlowFormatter
from rag5.utils.flow_logger import FlowLogger
import tempfile
import os


def create_sample_log():
    """Create a sample unified flow log for testing."""
    # Create temporary log file
    temp_dir = tempfile.mkdtemp()
    log_file = os.path.join(temp_dir, "test_flow.log")
    
    # Create a flow logger and log some events
    logger = FlowLogger(
        log_file=log_file,
        session_id="test-session-001",
        enabled=True,
        detail_level="normal",
        async_logging=False  # Synchronous for testing
    )
    
    # Log a complete query flow
    logger.log_query_start("What is the capital of France?")
    
    logger.log_query_analysis(
        detected_intent="factual_lookup",
        requires_tools=True,
        reasoning="Query asks for factual information that requires knowledge base search.",
        confidence=0.95
    )
    
    logger.log_tool_selection(
        tool_name="knowledge_base_search",
        rationale="Need to search knowledge base for factual information.",
        confidence=0.90
    )
    
    logger.log_tool_execution(
        tool_name="knowledge_base_search",
        tool_input="capital of France",
        tool_output="Paris is the capital and largest city of France.",
        duration_seconds=0.234,
        status="success"
    )
    
    logger.log_llm_call(
        model="qwen2.5:7b",
        prompt="Based on the context, answer: What is the capital of France?",
        response="The capital of France is Paris.",
        duration_seconds=1.567,
        token_usage={"prompt_tokens": 45, "completion_tokens": 12, "total_tokens": 57},
        status="success"
    )
    
    logger.log_query_complete(
        final_answer="The capital of France is Paris.",
        total_duration_seconds=2.123,
        status="success"
    )
    
    # Log another session with an error
    logger2 = FlowLogger(
        log_file=log_file,
        session_id="test-session-002",
        enabled=True,
        detail_level="normal",
        async_logging=False
    )
    
    logger2.log_query_start("What is the weather today?")
    
    logger2.log_error(
        error_type="ToolExecutionError",
        error_message="Failed to connect to weather API",
        stack_trace="Traceback (most recent call last):\n  File 'tool.py', line 45\n    raise ConnectionError()"
    )
    
    logger2.log_query_complete(
        final_answer="",
        total_duration_seconds=0.567,
        status="error"
    )
    
    # Log a slow operation
    logger3 = FlowLogger(
        log_file=log_file,
        session_id="test-session-003",
        enabled=True,
        detail_level="normal",
        async_logging=False
    )
    
    logger3.log_query_start("Complex query requiring multiple tools")
    
    logger3.log_tool_execution(
        tool_name="complex_search",
        tool_input="complex query",
        tool_output="Large result set...",
        duration_seconds=6.789,  # Slow operation
        status="success"
    )
    
    logger3.log_query_complete(
        final_answer="Complex answer",
        total_duration_seconds=8.234,
        status="success"
    )
    
    return log_file


def test_analyzer():
    """Test the FlowLogAnalyzer."""
    print("Creating sample log file...")
    log_file = create_sample_log()
    print(f"Sample log created at: {log_file}")
    
    print("\n" + "="*80)
    print("Testing FlowLogAnalyzer")
    print("="*80)
    
    # Initialize analyzer
    print("\n1. Initializing analyzer...")
    analyzer = FlowLogAnalyzer(log_file)
    print(f"   Loaded {len(analyzer.entries)} entries")
    
    # Test filter_by_session
    print("\n2. Testing filter_by_session()...")
    session_entries = analyzer.filter_by_session("test-session-001")
    print(f"   Found {len(session_entries)} entries for session 'test-session-001'")
    for entry in session_entries:
        print(f"   - {entry['event_type']}")
    
    # Test get_timing_stats
    print("\n3. Testing get_timing_stats()...")
    stats = analyzer.get_timing_stats()
    print(f"   Statistics calculated for {len(stats)} operation types:")
    for op_type, op_stats in stats.items():
        print(f"   - {op_type}:")
        print(f"     Count: {op_stats['count']}")
        print(f"     Average: {op_stats['avg']:.3f}s")
        print(f"     Min: {op_stats['min']:.3f}s")
        print(f"     Max: {op_stats['max']:.3f}s")
        print(f"     P95: {op_stats['p95']:.3f}s")
    
    # Test find_errors
    print("\n4. Testing find_errors()...")
    errors = analyzer.find_errors()
    print(f"   Found {len(errors)} errors:")
    for error in errors:
        print(f"   - Session: {error['session_id']}")
        print(f"     Type: {error['error_type']}")
        print(f"     Message: {error['error_message']}")
    
    # Test find_slow_operations
    print("\n5. Testing find_slow_operations()...")
    slow_ops = analyzer.find_slow_operations(threshold_seconds=5.0)
    print(f"   Found {len(slow_ops)} slow operations (>5s):")
    for op in slow_ops:
        print(f"   - {op['operation']}")
        print(f"     Duration: {op['duration']:.3f}s")
        print(f"     Session: {op['session_id']}")
    
    # Test export_to_json
    print("\n6. Testing export_to_json()...")
    json_file = log_file.replace('.log', '.json')
    analyzer.export_to_json(json_file)
    print(f"   Exported to: {json_file}")
    print(f"   File size: {Path(json_file).stat().st_size} bytes")
    
    # Test export_to_csv
    print("\n7. Testing export_to_csv()...")
    csv_file = log_file.replace('.log', '.csv')
    analyzer.export_to_csv(csv_file)
    print(f"   Exported to: {csv_file}")
    print(f"   File size: {Path(csv_file).stat().st_size} bytes")
    
    print("\n" + "="*80)
    print("All tests completed successfully!")
    print("="*80)
    
    # Show sample of exported files
    print("\nSample JSON output (first 500 chars):")
    with open(json_file, 'r') as f:
        content = f.read()
        print(content[:500] + "...")
    
    print("\nSample CSV output (first 10 lines):")
    with open(csv_file, 'r') as f:
        lines = f.readlines()
        for line in lines[:10]:
            print(line.rstrip())
    
    # Cleanup
    print(f"\nTest files created in: {Path(log_file).parent}")
    print("You can inspect them manually if needed.")


if __name__ == "__main__":
    test_analyzer()
