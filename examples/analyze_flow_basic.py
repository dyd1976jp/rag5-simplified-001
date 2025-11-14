#!/usr/bin/env python3
"""
Basic Flow Log Analysis Example

This example demonstrates how to:
1. Load and parse a unified flow log file
2. Filter entries by session ID
3. Extract timing statistics
4. Display basic information about queries

Requirements: 10.1, 10.2
"""

from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag5.utils.flow_analyzer import FlowLogAnalyzer


def main():
    """
    Main function demonstrating basic flow log analysis.
    """
    # Step 1: Initialize the analyzer with the log file path
    # The FlowLogAnalyzer automatically parses the log file on initialization
    log_file = "logs/unified_flow.log"
    
    print(f"Loading flow log from: {log_file}")
    print("=" * 80)
    
    try:
        analyzer = FlowLogAnalyzer(log_file)
    except Exception as e:
        print(f"Error loading log file: {e}")
        return
    
    # Step 2: Display basic information about the log
    print(f"\nTotal entries in log: {len(analyzer.entries)}")
    
    # Count entries by type
    event_types = {}
    sessions = set()
    
    for entry in analyzer.entries:
        event_type = entry['event_type']
        event_types[event_type] = event_types.get(event_type, 0) + 1
        
        if entry.get('session_id'):
            sessions.add(entry['session_id'])
    
    print(f"Unique sessions: {len(sessions)}")
    print("\nEvent type breakdown:")
    for event_type, count in sorted(event_types.items()):
        print(f"  {event_type}: {count}")
    
    # Step 3: Extract timing statistics
    # This calculates average, min, max, and p95 durations for different operation types
    print("\n" + "=" * 80)
    print("TIMING STATISTICS")
    print("=" * 80)
    
    stats = analyzer.get_timing_stats()
    
    if not stats:
        print("No timing statistics available (log may be empty)")
        return
    
    # Display tool execution statistics
    if 'tool_execution' in stats:
        tool_stats = stats['tool_execution']
        print("\nTool Execution Times:")
        print(f"  Count:   {tool_stats['count']}")
        print(f"  Average: {tool_stats['avg']:.3f}s")
        print(f"  Min:     {tool_stats['min']:.3f}s")
        print(f"  Max:     {tool_stats['max']:.3f}s")
        print(f"  P95:     {tool_stats['p95']:.3f}s")
    
    # Display LLM call statistics
    if 'llm_call' in stats:
        llm_stats = stats['llm_call']
        print("\nLLM Call Times:")
        print(f"  Count:   {llm_stats['count']}")
        print(f"  Average: {llm_stats['avg']:.3f}s")
        print(f"  Min:     {llm_stats['min']:.3f}s")
        print(f"  Max:     {llm_stats['max']:.3f}s")
        print(f"  P95:     {llm_stats['p95']:.3f}s")
    
    # Display total query time statistics
    if 'query_complete' in stats:
        query_stats = stats['query_complete']
        print("\nTotal Query Times:")
        print(f"  Count:   {query_stats['count']}")
        print(f"  Average: {query_stats['avg']:.3f}s")
        print(f"  Min:     {query_stats['min']:.3f}s")
        print(f"  Max:     {query_stats['max']:.3f}s")
        print(f"  P95:     {query_stats['p95']:.3f}s")
    
    # Step 4: Filter by session ID
    # This demonstrates how to extract all entries for a specific query session
    if sessions:
        print("\n" + "=" * 80)
        print("SESSION FILTERING EXAMPLE")
        print("=" * 80)
        
        # Get the first session ID as an example
        example_session = list(sessions)[0]
        print(f"\nFiltering entries for session: {example_session}")
        
        # Filter entries for this session
        session_entries = analyzer.filter_by_session(example_session)
        
        print(f"Found {len(session_entries)} entries for this session:")
        print()
        
        # Display each entry in the session
        for entry in session_entries:
            timestamp = entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if entry['timestamp'] else "N/A"
            event_type = entry['event_type']
            elapsed = f"+{entry['elapsed_time']:.3f}s" if entry.get('elapsed_time') is not None else ""
            
            print(f"  [{timestamp}] {event_type:20s} {elapsed}")
            
            # Show additional details for certain event types
            metadata = entry.get('metadata', {})
            if event_type in ('TOOL_EXECUTION', 'TOOL_EXEC') and 'tool_name' in metadata:
                print(f"    Tool: {metadata['tool_name']}")
                if 'duration' in metadata:
                    print(f"    Duration: {metadata['duration']:.3f}s")
            elif event_type == 'LLM_CALL' and 'model' in metadata:
                print(f"    Model: {metadata['model']}")
                if 'duration' in metadata:
                    print(f"    Duration: {metadata['duration']:.3f}s")
            elif event_type == 'ERROR':
                if 'error_type' in metadata:
                    print(f"    Error Type: {metadata['error_type']}")
                if 'error_message' in metadata:
                    print(f"    Message: {metadata['error_message']}")
    
    # Step 5: Summary
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nThis example demonstrated:")
    print("  ✓ Loading and parsing a flow log file")
    print("  ✓ Extracting timing statistics")
    print("  ✓ Filtering entries by session ID")
    print("  ✓ Displaying structured information")
    print("\nFor more advanced analysis, see:")
    print("  - analyze_flow_errors.py (error analysis)")
    print("  - analyze_flow_performance.py (performance analysis)")


if __name__ == "__main__":
    main()
