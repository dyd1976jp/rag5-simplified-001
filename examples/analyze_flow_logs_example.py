"""
Example: Analyzing unified flow logs.

This example demonstrates how to use FlowLogAnalyzer to analyze
unified flow logs and extract useful information.
"""

from rag5.utils import FlowLogAnalyzer
from pathlib import Path


def main():
    """Main example function."""
    # Path to unified flow log
    log_file = "logs/unified_flow.log"
    
    # Check if log file exists
    if not Path(log_file).exists():
        print(f"Log file not found: {log_file}")
        print("Please run some queries first to generate logs.")
        return
    
    print("="*80)
    print("Unified Flow Log Analysis Example")
    print("="*80)
    
    # Initialize analyzer
    print(f"\nAnalyzing log file: {log_file}")
    analyzer = FlowLogAnalyzer(log_file)
    print(f"Loaded {len(analyzer.entries)} log entries")
    
    # Get all unique sessions
    sessions = set(entry.get('session_id') for entry in analyzer.entries if entry.get('session_id'))
    print(f"Found {len(sessions)} unique sessions")
    
    # Example 1: Filter by session
    if sessions:
        session_id = list(sessions)[0]
        print(f"\n--- Example 1: Filter by Session ---")
        print(f"Session ID: {session_id}")
        
        session_entries = analyzer.filter_by_session(session_id)
        print(f"Found {len(session_entries)} entries for this session:")
        for entry in session_entries:
            print(f"  - {entry['event_type']} at +{entry.get('elapsed_time', 0):.3f}s")
    
    # Example 2: Get timing statistics
    print(f"\n--- Example 2: Timing Statistics ---")
    stats = analyzer.get_timing_stats()
    
    for op_type, op_stats in stats.items():
        print(f"\n{op_type.replace('_', ' ').title()}:")
        print(f"  Count:   {op_stats['count']}")
        print(f"  Average: {op_stats['avg']:.3f}s")
        print(f"  Min:     {op_stats['min']:.3f}s")
        print(f"  Max:     {op_stats['max']:.3f}s")
        print(f"  P95:     {op_stats['p95']:.3f}s")
    
    # Example 3: Find errors
    print(f"\n--- Example 3: Find Errors ---")
    errors = analyzer.find_errors()
    
    if errors:
        print(f"Found {len(errors)} errors:")
        for error in errors:
            print(f"\n  Error in session: {error['session_id']}")
            print(f"  Type: {error['error_type']}")
            print(f"  Message: {error['error_message']}")
            print(f"  Time: {error['elapsed_time']:.3f}s")
    else:
        print("No errors found!")
    
    # Example 4: Find slow operations
    print(f"\n--- Example 4: Find Slow Operations (>2s) ---")
    slow_ops = analyzer.find_slow_operations(threshold_seconds=2.0)
    
    if slow_ops:
        print(f"Found {len(slow_ops)} slow operations:")
        for op in slow_ops:
            print(f"\n  {op['operation']}")
            print(f"  Duration: {op['duration']:.3f}s")
            print(f"  Session: {op['session_id']}")
    else:
        print("No slow operations found!")
    
    # Example 5: Export to JSON
    print(f"\n--- Example 5: Export to JSON ---")
    json_file = "logs/flow_analysis.json"
    analyzer.export_to_json(json_file)
    print(f"Exported to: {json_file}")
    
    # Example 6: Export to CSV
    print(f"\n--- Example 6: Export to CSV ---")
    csv_file = "logs/flow_analysis.csv"
    analyzer.export_to_csv(csv_file)
    print(f"Exported to: {csv_file}")
    
    print("\n" + "="*80)
    print("Analysis complete!")
    print("="*80)


if __name__ == "__main__":
    main()
