#!/usr/bin/env python3
"""
Performance Analysis Example for Flow Logs

This example demonstrates how to:
1. Find slow operations in the log
2. Analyze performance trends
3. Identify bottlenecks
4. Generate performance reports

Requirements: 10.2, 10.3
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
    Main function demonstrating performance analysis in flow logs.
    """
    # Step 1: Initialize the analyzer
    log_file = "logs/unified_flow.log"
    
    print(f"Analyzing performance in: {log_file}")
    print("=" * 80)
    
    try:
        analyzer = FlowLogAnalyzer(log_file)
    except Exception as e:
        print(f"Error loading log file: {e}")
        return
    
    if not analyzer.entries:
        print("No entries found in log file.")
        return
    
    # Step 2: Get overall timing statistics
    # This provides a baseline for performance analysis
    print("\n" + "=" * 80)
    print("OVERALL PERFORMANCE STATISTICS")
    print("=" * 80)
    
    stats = analyzer.get_timing_stats()
    
    if not stats:
        print("No timing statistics available.")
        return
    
    # Display comprehensive statistics
    for operation_type, operation_stats in stats.items():
        print(f"\n{operation_type.replace('_', ' ').title()}:")
        print(f"  Total operations: {operation_stats['count']}")
        print(f"  Average time:     {operation_stats['avg']:.3f}s")
        print(f"  Minimum time:     {operation_stats['min']:.3f}s")
        print(f"  Maximum time:     {operation_stats['max']:.3f}s")
        print(f"  95th percentile:  {operation_stats['p95']:.3f}s")
        
        # Provide performance assessment
        if operation_type == 'query_complete':
            if operation_stats['avg'] < 2.0:
                print("  ✓ Excellent average response time")
            elif operation_stats['avg'] < 5.0:
                print("  ✓ Good average response time")
            elif operation_stats['avg'] < 10.0:
                print("  ⚠ Moderate average response time")
            else:
                print("  ⚠ Slow average response time - investigate bottlenecks")
        
        elif operation_type == 'llm_call':
            if operation_stats['avg'] < 1.0:
                print("  ✓ Fast LLM responses")
            elif operation_stats['avg'] < 3.0:
                print("  ✓ Normal LLM response times")
            else:
                print("  ⚠ Slow LLM responses - consider model optimization")
        
        elif operation_type == 'tool_execution':
            if operation_stats['avg'] < 0.5:
                print("  ✓ Fast tool execution")
            elif operation_stats['avg'] < 2.0:
                print("  ✓ Normal tool execution times")
            else:
                print("  ⚠ Slow tool execution - review tool implementations")
    
    # Step 3: Find slow operations
    # Use different thresholds for different operation types
    print("\n" + "=" * 80)
    print("SLOW OPERATIONS ANALYSIS")
    print("=" * 80)
    
    # Define thresholds for what constitutes "slow"
    thresholds = {
        'query': 10.0,      # Queries over 10 seconds
        'llm': 5.0,         # LLM calls over 5 seconds
        'tool': 3.0         # Tool executions over 3 seconds
    }
    
    print(f"\nSearching for operations exceeding thresholds:")
    print(f"  Query completion: > {thresholds['query']}s")
    print(f"  LLM calls:        > {thresholds['llm']}s")
    print(f"  Tool execution:   > {thresholds['tool']}s")
    
    # Find slow queries
    slow_queries = analyzer.find_slow_operations(threshold_seconds=thresholds['query'])
    slow_queries = [op for op in slow_queries if op['event_type'] in ('QUERY_COMPLETE', 'COMPLETE')]
    
    # Find slow LLM calls
    slow_llm = analyzer.find_slow_operations(threshold_seconds=thresholds['llm'])
    slow_llm = [op for op in slow_llm if op['event_type'] == 'LLM_CALL']
    
    # Find slow tool executions
    slow_tools = analyzer.find_slow_operations(threshold_seconds=thresholds['tool'])
    slow_tools = [op for op in slow_tools if op['event_type'] in ('TOOL_EXECUTION', 'TOOL_EXEC')]
    
    print(f"\nResults:")
    print(f"  Slow queries:        {len(slow_queries)}")
    print(f"  Slow LLM calls:      {len(slow_llm)}")
    print(f"  Slow tool executions: {len(slow_tools)}")
    
    # Step 4: Analyze slow operations in detail
    if slow_queries:
        print("\n" + "─" * 80)
        print("SLOW QUERIES")
        print("─" * 80)
        
        for idx, op in enumerate(slow_queries, 1):
            timestamp = op['timestamp'].strftime("%Y-%m-%d %H:%M:%S") if op['timestamp'] else "N/A"
            print(f"\n  Query #{idx}:")
            print(f"    Timestamp: {timestamp}")
            print(f"    Session:   {op.get('session_id', 'N/A')}")
            print(f"    Duration:  {op['duration']:.3f}s (threshold: {op['threshold']}s)")
            print(f"    Slowdown:  {(op['duration'] / op['threshold']):.1f}x over threshold")
    
    if slow_llm:
        print("\n" + "─" * 80)
        print("SLOW LLM CALLS")
        print("─" * 80)
        
        for idx, op in enumerate(slow_llm, 1):
            timestamp = op['timestamp'].strftime("%Y-%m-%d %H:%M:%S") if op['timestamp'] else "N/A"
            print(f"\n  LLM Call #{idx}:")
            print(f"    Timestamp: {timestamp}")
            print(f"    Session:   {op.get('session_id', 'N/A')}")
            print(f"    Operation: {op['operation']}")
            print(f"    Duration:  {op['duration']:.3f}s (threshold: {op['threshold']}s)")
    
    if slow_tools:
        print("\n" + "─" * 80)
        print("SLOW TOOL EXECUTIONS")
        print("─" * 80)
        
        for idx, op in enumerate(slow_tools, 1):
            timestamp = op['timestamp'].strftime("%Y-%m-%d %H:%M:%S") if op['timestamp'] else "N/A"
            print(f"\n  Tool Execution #{idx}:")
            print(f"    Timestamp: {timestamp}")
            print(f"    Session:   {op.get('session_id', 'N/A')}")
            print(f"    Operation: {op['operation']}")
            print(f"    Duration:  {op['duration']:.3f}s (threshold: {op['threshold']}s)")
    
    # Step 5: Identify bottlenecks
    # Analyze where time is being spent in query processing
    print("\n" + "=" * 80)
    print("BOTTLENECK ANALYSIS")
    print("=" * 80)
    
    bottlenecks = identify_bottlenecks(analyzer, stats)
    
    if bottlenecks:
        print("\nIdentified bottlenecks (ordered by impact):")
        for idx, bottleneck in enumerate(bottlenecks, 1):
            print(f"\n  {idx}. {bottleneck['component']}")
            print(f"     Average time: {bottleneck['avg_time']:.3f}s")
            print(f"     % of total:   {bottleneck['percentage']:.1f}%")
            print(f"     Impact:       {bottleneck['impact']}")
            print(f"     Recommendation: {bottleneck['recommendation']}")
    else:
        print("\n✓ No significant bottlenecks identified")
        print("  Performance appears well-balanced across components")
    
    # Step 6: Performance trends
    # Analyze if performance is degrading over time
    print("\n" + "=" * 80)
    print("PERFORMANCE TRENDS")
    print("=" * 80)
    
    trends = analyze_performance_trends(analyzer)
    
    if trends:
        print("\nPerformance over time:")
        
        for component, trend_data in trends.items():
            print(f"\n  {component.replace('_', ' ').title()}:")
            
            if trend_data['trend'] == 'improving':
                print(f"    ✓ Performance is improving")
                print(f"      Early avg: {trend_data['early_avg']:.3f}s")
                print(f"      Recent avg: {trend_data['recent_avg']:.3f}s")
                print(f"      Change: {trend_data['change']:.1f}%")
            elif trend_data['trend'] == 'degrading':
                print(f"    ⚠ Performance is degrading")
                print(f"      Early avg: {trend_data['early_avg']:.3f}s")
                print(f"      Recent avg: {trend_data['recent_avg']:.3f}s")
                print(f"      Change: +{trend_data['change']:.1f}%")
            else:
                print(f"    → Performance is stable")
                print(f"      Average: {trend_data['early_avg']:.3f}s")
    else:
        print("\nInsufficient data for trend analysis")
        print("  (Need at least 10 operations)")
    
    # Step 7: Generate performance report summary
    print("\n" + "=" * 80)
    print("PERFORMANCE REPORT SUMMARY")
    print("=" * 80)
    
    generate_performance_summary(stats, slow_queries, slow_llm, slow_tools, bottlenecks)


def identify_bottlenecks(analyzer: FlowLogAnalyzer, stats: dict) -> list:
    """
    Identify performance bottlenecks by analyzing time distribution.
    
    Args:
        analyzer: FlowLogAnalyzer instance
        stats: Timing statistics
        
    Returns:
        List of bottlenecks ordered by impact
    """
    bottlenecks = []
    
    # Calculate total average query time
    if 'query_complete' not in stats:
        return bottlenecks
    
    total_avg = stats['query_complete']['avg']
    
    # Analyze LLM time contribution
    if 'llm_call' in stats:
        llm_avg = stats['llm_call']['avg']
        llm_percentage = (llm_avg / total_avg) * 100 if total_avg > 0 else 0
        
        if llm_percentage > 60:
            bottlenecks.append({
                'component': 'LLM Calls',
                'avg_time': llm_avg,
                'percentage': llm_percentage,
                'impact': 'High',
                'recommendation': 'Consider using a faster model or optimizing prompts'
            })
        elif llm_percentage > 40:
            bottlenecks.append({
                'component': 'LLM Calls',
                'avg_time': llm_avg,
                'percentage': llm_percentage,
                'impact': 'Moderate',
                'recommendation': 'LLM time is significant but acceptable'
            })
    
    # Analyze tool execution time contribution
    if 'tool_execution' in stats:
        tool_avg = stats['tool_execution']['avg']
        tool_percentage = (tool_avg / total_avg) * 100 if total_avg > 0 else 0
        
        if tool_percentage > 40:
            bottlenecks.append({
                'component': 'Tool Execution',
                'avg_time': tool_avg,
                'percentage': tool_percentage,
                'impact': 'High',
                'recommendation': 'Optimize tool implementations or add caching'
            })
        elif tool_percentage > 25:
            bottlenecks.append({
                'component': 'Tool Execution',
                'avg_time': tool_avg,
                'percentage': tool_percentage,
                'impact': 'Moderate',
                'recommendation': 'Consider tool optimization if queries are slow'
            })
    
    # Sort by percentage (impact)
    bottlenecks.sort(key=lambda x: x['percentage'], reverse=True)
    
    return bottlenecks


def analyze_performance_trends(analyzer: FlowLogAnalyzer) -> dict:
    """
    Analyze performance trends over time.
    
    Args:
        analyzer: FlowLogAnalyzer instance
        
    Returns:
        Dictionary of trends by component
    """
    trends = {}
    
    # Group entries by type and collect durations with timestamps
    operation_data = defaultdict(list)
    
    for entry in analyzer.entries:
        event_type = entry['event_type']
        metadata = entry.get('metadata', {})
        timestamp = entry.get('timestamp')
        
        if not timestamp:
            continue
        
        duration = None
        operation_key = None
        
        if event_type in ('TOOL_EXECUTION', 'TOOL_EXEC'):
            duration = metadata.get('duration')
            operation_key = 'tool_execution'
        elif event_type == 'LLM_CALL':
            duration = metadata.get('duration')
            operation_key = 'llm_call'
        elif event_type in ('QUERY_COMPLETE', 'COMPLETE'):
            duration = metadata.get('total_duration') or entry.get('elapsed_time')
            operation_key = 'query_complete'
        
        if duration is not None and operation_key:
            operation_data[operation_key].append((timestamp, duration))
    
    # Analyze trends for each operation type
    for operation_key, data_points in operation_data.items():
        if len(data_points) < 10:
            continue  # Need sufficient data for trend analysis
        
        # Sort by timestamp
        data_points.sort(key=lambda x: x[0])
        
        # Split into early and recent halves
        mid_point = len(data_points) // 2
        early_durations = [d for _, d in data_points[:mid_point]]
        recent_durations = [d for _, d in data_points[mid_point:]]
        
        early_avg = sum(early_durations) / len(early_durations)
        recent_avg = sum(recent_durations) / len(recent_durations)
        
        # Calculate change percentage
        change = ((recent_avg - early_avg) / early_avg * 100) if early_avg > 0 else 0
        
        # Determine trend
        if change < -10:
            trend = 'improving'
        elif change > 10:
            trend = 'degrading'
        else:
            trend = 'stable'
        
        trends[operation_key] = {
            'trend': trend,
            'early_avg': early_avg,
            'recent_avg': recent_avg,
            'change': abs(change)
        }
    
    return trends


def generate_performance_summary(stats: dict, slow_queries: list, slow_llm: list, 
                                 slow_tools: list, bottlenecks: list) -> None:
    """
    Generate a summary of performance analysis.
    
    Args:
        stats: Timing statistics
        slow_queries: List of slow queries
        slow_llm: List of slow LLM calls
        slow_tools: List of slow tool executions
        bottlenecks: List of identified bottlenecks
    """
    print("\nKey Findings:")
    
    # Overall performance assessment
    if 'query_complete' in stats:
        avg_time = stats['query_complete']['avg']
        if avg_time < 3.0:
            print("  ✓ Overall performance is excellent")
        elif avg_time < 7.0:
            print("  ✓ Overall performance is good")
        else:
            print("  ⚠ Overall performance needs improvement")
    
    # Slow operations summary
    total_slow = len(slow_queries) + len(slow_llm) + len(slow_tools)
    if total_slow == 0:
        print("  ✓ No slow operations detected")
    else:
        print(f"  ⚠ {total_slow} slow operation(s) detected")
    
    # Bottleneck summary
    if bottlenecks:
        print(f"  ⚠ {len(bottlenecks)} bottleneck(s) identified")
        print(f"    Primary bottleneck: {bottlenecks[0]['component']}")
    else:
        print("  ✓ No significant bottlenecks")
    
    print("\nRecommendations:")
    
    if not bottlenecks and total_slow == 0:
        print("  • System performance is healthy")
        print("  • Continue monitoring for trends")
    else:
        if slow_queries:
            print("  • Investigate slow queries to identify patterns")
        if slow_llm:
            print("  • Consider LLM optimization (model selection, prompt engineering)")
        if slow_tools:
            print("  • Review and optimize tool implementations")
        if bottlenecks:
            print(f"  • Focus optimization efforts on: {bottlenecks[0]['component']}")
    
    print("\nNext Steps:")
    print("  1. Review detailed analysis sections above")
    print("  2. Investigate specific slow operations")
    print("  3. Implement recommended optimizations")
    print("  4. Re-run analysis to measure improvements")


if __name__ == "__main__":
    main()
