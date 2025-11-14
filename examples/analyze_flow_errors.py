#!/usr/bin/env python3
"""
Error Analysis Example for Flow Logs

This example demonstrates how to:
1. Find all errors in the flow log
2. Group errors by type
3. Extract error context (what was happening when error occurred)
4. Identify patterns in errors

Requirements: 10.3
"""

from pathlib import Path
import sys
from collections import defaultdict
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag5.utils.flow_analyzer import FlowLogAnalyzer


def main():
    """
    Main function demonstrating error analysis in flow logs.
    """
    # Step 1: Initialize the analyzer
    log_file = "logs/unified_flow.log"
    
    print(f"Analyzing errors in: {log_file}")
    print("=" * 80)
    
    try:
        analyzer = FlowLogAnalyzer(log_file)
    except Exception as e:
        print(f"Error loading log file: {e}")
        return
    
    # Step 2: Find all errors in the log
    # The find_errors() method extracts all ERROR entries with their context
    print("\nSearching for errors...")
    errors = analyzer.find_errors()
    
    if not errors:
        print("✓ No errors found in the log!")
        print("\nThis is good news - all queries completed successfully.")
        return
    
    print(f"Found {len(errors)} error(s)")
    
    # Step 3: Group errors by type
    # This helps identify common failure patterns
    print("\n" + "=" * 80)
    print("ERROR GROUPING BY TYPE")
    print("=" * 80)
    
    errors_by_type = defaultdict(list)
    
    for error in errors:
        error_type = error.get('error_type', 'Unknown')
        errors_by_type[error_type].append(error)
    
    # Display error counts by type
    print("\nError type breakdown:")
    for error_type, error_list in sorted(errors_by_type.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {error_type}: {len(error_list)} occurrence(s)")
    
    # Step 4: Display detailed information for each error type
    print("\n" + "=" * 80)
    print("DETAILED ERROR ANALYSIS")
    print("=" * 80)
    
    for error_type, error_list in sorted(errors_by_type.items()):
        print(f"\n{'─' * 80}")
        print(f"Error Type: {error_type}")
        print(f"Occurrences: {len(error_list)}")
        print(f"{'─' * 80}")
        
        # Show details for each occurrence
        for idx, error in enumerate(error_list, 1):
            print(f"\n  Occurrence #{idx}:")
            
            # Timestamp
            if error.get('timestamp'):
                timestamp = error['timestamp'].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                print(f"    Timestamp: {timestamp}")
            
            # Session ID
            if error.get('session_id'):
                print(f"    Session:   {error['session_id']}")
            
            # Elapsed time (how long into the query the error occurred)
            if error.get('elapsed_time') is not None:
                print(f"    Elapsed:   {error['elapsed_time']:.3f}s into query")
            
            # Error message
            if error.get('error_message'):
                print(f"    Message:   {error['error_message']}")
            
            # Step 5: Extract error context
            # Show what was happening before the error occurred
            if error.get('session_id'):
                print(f"\n    Context (events before error):")
                context = get_error_context(analyzer, error['session_id'], error['timestamp'])
                
                if context:
                    for ctx_entry in context[-3:]:  # Show last 3 events before error
                        event_type = ctx_entry['event_type']
                        elapsed = f"+{ctx_entry['elapsed_time']:.3f}s" if ctx_entry.get('elapsed_time') is not None else ""
                        print(f"      → {event_type:20s} {elapsed}")
                        
                        # Show operation details
                        metadata = ctx_entry.get('metadata', {})
                        if event_type in ('TOOL_EXECUTION', 'TOOL_EXEC') and 'tool_name' in metadata:
                            print(f"        Tool: {metadata['tool_name']}")
                        elif event_type == 'LLM_CALL' and 'model' in metadata:
                            print(f"        Model: {metadata['model']}")
                else:
                    print("      (No prior events in session)")
    
    # Step 6: Identify error patterns
    print("\n" + "=" * 80)
    print("ERROR PATTERNS")
    print("=" * 80)
    
    # Check if errors occur at similar times in query processing
    error_timings = [e['elapsed_time'] for e in errors if e.get('elapsed_time') is not None]
    
    if error_timings:
        avg_timing = sum(error_timings) / len(error_timings)
        print(f"\nAverage time to error: {avg_timing:.3f}s")
        
        # Check if errors happen early or late in processing
        if avg_timing < 1.0:
            print("  → Errors tend to occur early in query processing")
            print("    (May indicate validation or initialization issues)")
        elif avg_timing > 5.0:
            print("  → Errors tend to occur late in query processing")
            print("    (May indicate timeout or resource exhaustion issues)")
        else:
            print("  → Errors occur during mid-processing")
            print("    (May indicate tool execution or LLM call issues)")
    
    # Check if errors are concentrated in specific sessions
    sessions_with_errors = set(e['session_id'] for e in errors if e.get('session_id'))
    total_sessions = len(set(e.get('session_id') for e in analyzer.entries if e.get('session_id')))
    
    if total_sessions > 0:
        error_rate = len(sessions_with_errors) / total_sessions * 100
        print(f"\nError rate: {error_rate:.1f}% of sessions had errors")
        print(f"  ({len(sessions_with_errors)} out of {total_sessions} sessions)")
        
        if error_rate > 50:
            print("  ⚠ High error rate - investigate system health")
        elif error_rate > 20:
            print("  ⚠ Moderate error rate - review error patterns")
        else:
            print("  ✓ Low error rate - errors appear to be isolated incidents")
    
    # Step 7: Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    print("\nBased on the error analysis:")
    
    # Provide specific recommendations based on error types
    if 'ConnectionError' in errors_by_type or 'TimeoutError' in errors_by_type:
        print("  • Check network connectivity and service availability")
        print("  • Review timeout settings")
    
    if 'ToolExecutionError' in errors_by_type:
        print("  • Review tool configurations and dependencies")
        print("  • Verify tool inputs are valid")
    
    if 'ValidationError' in errors_by_type:
        print("  • Review input validation logic")
        print("  • Check for edge cases in user queries")
    
    if len(errors_by_type) == 1:
        print("  • Errors are concentrated in one type - focus investigation there")
    else:
        print("  • Multiple error types - may indicate systemic issues")
    
    print("\n  For detailed error context, review the raw log entries above.")


def get_error_context(analyzer: FlowLogAnalyzer, session_id: str, error_timestamp: datetime) -> list:
    """
    Get events that occurred before an error in the same session.
    
    This helps understand what was happening when the error occurred.
    
    Args:
        analyzer: FlowLogAnalyzer instance
        session_id: Session ID of the error
        error_timestamp: Timestamp of the error
        
    Returns:
        List of entries that occurred before the error
    """
    # Get all entries for this session
    session_entries = analyzer.filter_by_session(session_id)
    
    # Filter to entries before the error
    context = []
    for entry in session_entries:
        if entry['event_type'] == 'ERROR':
            continue  # Skip error entries
        
        if entry.get('timestamp') and error_timestamp:
            if entry['timestamp'] < error_timestamp:
                context.append(entry)
    
    # Sort by timestamp
    context.sort(key=lambda x: x.get('timestamp') or datetime.min)
    
    return context


if __name__ == "__main__":
    main()
