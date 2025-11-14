#!/usr/bin/env python3
"""
LLM Log Analyzer

This script analyzes LLM interaction logs to extract insights about:
- Request/response timing statistics
- Token usage patterns
- Error rates and types
- Slow requests
- Model usage distribution

Usage:
    python examples/analyze_llm_logs.py
    python examples/analyze_llm_logs.py --log-file logs/llm_interactions.log
    python examples/analyze_llm_logs.py --session-id session-xyz-789
    python examples/analyze_llm_logs.py --slow-threshold 5.0
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import statistics


class LLMLogAnalyzer:
    """Analyzes LLM interaction logs"""
    
    def __init__(self, log_file: str):
        self.log_file = Path(log_file)
        self.entries = []
        self._load_logs()
    
    def _load_logs(self):
        """Load and parse log file"""
        if not self.log_file.exists():
            print(f"Warning: Log file {self.log_file} does not exist")
            return
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    self.entries.append(entry)
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line: {e}")
    
    def get_requests(self) -> List[Dict[str, Any]]:
        """Get all LLM request entries"""
        return [e for e in self.entries if e.get('log_type') == 'llm_request']
    
    def get_responses(self) -> List[Dict[str, Any]]:
        """Get all LLM response entries"""
        return [e for e in self.entries if e.get('log_type') == 'llm_response']
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """Get all error entries"""
        return [e for e in self.entries 
                if e.get('log_type') == 'llm_response' 
                and e.get('data', {}).get('status') == 'error']
    
    def get_request_response_pair(self, request_id: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Get request and response for a given request_id"""
        request = None
        response = None
        
        for entry in self.entries:
            if entry.get('request_id') == request_id:
                if entry.get('log_type') == 'llm_request':
                    request = entry
                elif entry.get('log_type') == 'llm_response':
                    response = entry
        
        return request, response
    
    def get_session_entries(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all entries for a specific session"""
        return [e for e in self.entries if e.get('session_id') == session_id]
    
    def get_timing_stats(self) -> Dict[str, float]:
        """Calculate timing statistics"""
        responses = self.get_responses()
        durations = [r.get('data', {}).get('duration_seconds', 0) 
                    for r in responses 
                    if r.get('data', {}).get('status') == 'success']
        
        if not durations:
            return {
                'count': 0,
                'avg_duration': 0,
                'min_duration': 0,
                'max_duration': 0,
                'median_duration': 0,
                'p95_duration': 0,
                'p99_duration': 0
            }
        
        durations.sort()
        
        return {
            'count': len(durations),
            'avg_duration': statistics.mean(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'median_duration': statistics.median(durations),
            'p95_duration': durations[int(len(durations) * 0.95)] if len(durations) > 1 else durations[0],
            'p99_duration': durations[int(len(durations) * 0.99)] if len(durations) > 1 else durations[0]
        }
    
    def get_token_stats(self) -> Dict[str, Any]:
        """Calculate token usage statistics"""
        responses = self.get_responses()
        
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        count = 0
        
        for response in responses:
            token_usage = response.get('data', {}).get('token_usage')
            if token_usage:
                total_prompt_tokens += token_usage.get('prompt_tokens', 0)
                total_completion_tokens += token_usage.get('completion_tokens', 0)
                total_tokens += token_usage.get('total_tokens', 0)
                count += 1
        
        return {
            'total_requests': count,
            'total_prompt_tokens': total_prompt_tokens,
            'total_completion_tokens': total_completion_tokens,
            'total_tokens': total_tokens,
            'avg_prompt_tokens': total_prompt_tokens / count if count > 0 else 0,
            'avg_completion_tokens': total_completion_tokens / count if count > 0 else 0,
            'avg_total_tokens': total_tokens / count if count > 0 else 0
        }
    
    def find_slow_requests(self, threshold: float = 5.0) -> List[Dict[str, Any]]:
        """Find requests that took longer than threshold seconds"""
        responses = self.get_responses()
        slow = []
        
        for response in responses:
            duration = response.get('data', {}).get('duration_seconds', 0)
            if duration > threshold:
                request_id = response.get('request_id')
                request, _ = self.get_request_response_pair(request_id)
                slow.append({
                    'request_id': request_id,
                    'duration': duration,
                    'timestamp': response.get('timestamp'),
                    'model': request.get('data', {}).get('model') if request else None,
                    'prompt_length': request.get('data', {}).get('prompt_length') if request else None
                })
        
        return sorted(slow, key=lambda x: x['duration'], reverse=True)
    
    def get_model_distribution(self) -> Dict[str, int]:
        """Get distribution of requests by model"""
        requests = self.get_requests()
        distribution = defaultdict(int)
        
        for request in requests:
            model = request.get('data', {}).get('model', 'unknown')
            distribution[model] += 1
        
        return dict(distribution)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors"""
        errors = self.get_errors()
        total_responses = len(self.get_responses())
        
        error_types = defaultdict(int)
        for error in errors:
            error_msg = error.get('data', {}).get('error', 'unknown')
            # Extract error type from message
            error_type = error_msg.split(':')[0] if ':' in error_msg else error_msg
            error_types[error_type] += 1
        
        return {
            'total_errors': len(errors),
            'total_responses': total_responses,
            'error_rate': len(errors) / total_responses if total_responses > 0 else 0,
            'error_types': dict(error_types)
        }
    
    def print_summary(self):
        """Print comprehensive summary"""
        print("=" * 80)
        print("LLM LOG ANALYSIS SUMMARY")
        print("=" * 80)
        print(f"Log file: {self.log_file}")
        print(f"Total entries: {len(self.entries)}")
        print()
        
        # Request/Response counts
        requests = self.get_requests()
        responses = self.get_responses()
        print(f"Total requests: {len(requests)}")
        print(f"Total responses: {len(responses)}")
        print()
        
        # Timing statistics
        print("-" * 80)
        print("TIMING STATISTICS")
        print("-" * 80)
        timing = self.get_timing_stats()
        print(f"Successful requests: {timing['count']}")
        print(f"Average duration: {timing['avg_duration']:.3f}s")
        print(f"Median duration: {timing['median_duration']:.3f}s")
        print(f"Min duration: {timing['min_duration']:.3f}s")
        print(f"Max duration: {timing['max_duration']:.3f}s")
        print(f"95th percentile: {timing['p95_duration']:.3f}s")
        print(f"99th percentile: {timing['p99_duration']:.3f}s")
        print()
        
        # Token statistics
        print("-" * 80)
        print("TOKEN USAGE STATISTICS")
        print("-" * 80)
        tokens = self.get_token_stats()
        print(f"Total requests with token data: {tokens['total_requests']}")
        print(f"Total prompt tokens: {tokens['total_prompt_tokens']:,}")
        print(f"Total completion tokens: {tokens['total_completion_tokens']:,}")
        print(f"Total tokens: {tokens['total_tokens']:,}")
        print(f"Average prompt tokens: {tokens['avg_prompt_tokens']:.0f}")
        print(f"Average completion tokens: {tokens['avg_completion_tokens']:.0f}")
        print(f"Average total tokens: {tokens['avg_total_tokens']:.0f}")
        print()
        
        # Model distribution
        print("-" * 80)
        print("MODEL DISTRIBUTION")
        print("-" * 80)
        models = self.get_model_distribution()
        for model, count in sorted(models.items(), key=lambda x: x[1], reverse=True):
            print(f"{model}: {count} requests")
        print()
        
        # Error summary
        print("-" * 80)
        print("ERROR SUMMARY")
        print("-" * 80)
        errors = self.get_error_summary()
        print(f"Total errors: {errors['total_errors']}")
        print(f"Error rate: {errors['error_rate']:.2%}")
        if errors['error_types']:
            print("Error types:")
            for error_type, count in sorted(errors['error_types'].items(), 
                                           key=lambda x: x[1], reverse=True):
                print(f"  {error_type}: {count}")
        print()
        
        # Slow requests
        print("-" * 80)
        print("SLOW REQUESTS (> 5s)")
        print("-" * 80)
        slow = self.find_slow_requests(threshold=5.0)
        if slow:
            for req in slow[:10]:  # Show top 10
                print(f"Request {req['request_id'][:8]}...")
                print(f"  Duration: {req['duration']:.2f}s")
                print(f"  Model: {req['model']}")
                print(f"  Prompt length: {req['prompt_length']} chars")
                print(f"  Timestamp: {req['timestamp']}")
                print()
        else:
            print("No slow requests found")
        
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze LLM interaction logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze default log file
  python examples/analyze_llm_logs.py
  
  # Analyze specific log file
  python examples/analyze_llm_logs.py --log-file logs/llm_interactions.log
  
  # Find slow requests (> 10 seconds)
  python examples/analyze_llm_logs.py --slow-threshold 10.0
  
  # Analyze specific session
  python examples/analyze_llm_logs.py --session-id session-xyz-789
  
  # Get request/response pair
  python examples/analyze_llm_logs.py --request-id a1b2c3d4-e5f6-7890
        """
    )
    
    parser.add_argument(
        '--log-file',
        default='logs/llm_interactions.log',
        help='Path to LLM interaction log file (default: logs/llm_interactions.log)'
    )
    
    parser.add_argument(
        '--session-id',
        help='Analyze specific session'
    )
    
    parser.add_argument(
        '--request-id',
        help='Show request/response pair for specific request ID'
    )
    
    parser.add_argument(
        '--slow-threshold',
        type=float,
        default=5.0,
        help='Threshold for slow requests in seconds (default: 5.0)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    args = parser.parse_args()
    
    analyzer = LLMLogAnalyzer(args.log_file)
    
    if args.request_id:
        # Show specific request/response pair
        request, response = analyzer.get_request_response_pair(args.request_id)
        if request:
            print("REQUEST:")
            print(json.dumps(request, indent=2, ensure_ascii=False))
            print()
        if response:
            print("RESPONSE:")
            print(json.dumps(response, indent=2, ensure_ascii=False))
        if not request and not response:
            print(f"No entries found for request_id: {args.request_id}")
    
    elif args.session_id:
        # Show session entries
        entries = analyzer.get_session_entries(args.session_id)
        print(f"Found {len(entries)} entries for session {args.session_id}")
        print()
        for entry in entries:
            print(json.dumps(entry, indent=2, ensure_ascii=False))
            print()
    
    elif args.json:
        # Output as JSON
        result = {
            'timing': analyzer.get_timing_stats(),
            'tokens': analyzer.get_token_stats(),
            'models': analyzer.get_model_distribution(),
            'errors': analyzer.get_error_summary(),
            'slow_requests': analyzer.find_slow_requests(args.slow_threshold)
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        # Print summary
        analyzer.print_summary()


if __name__ == '__main__':
    main()
