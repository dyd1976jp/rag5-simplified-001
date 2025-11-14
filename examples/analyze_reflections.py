#!/usr/bin/env python3
"""
Agent Reflection Log Analyzer

This script analyzes agent reflection logs to understand:
- Query analysis and intent detection
- Tool selection decisions
- Query reformulation patterns
- Document relevance evaluation
- Answer synthesis reasoning

Usage:
    python examples/analyze_reflections.py
    python examples/analyze_reflections.py --log-file logs/agent_reflections.log
    python examples/analyze_reflections.py --session-id session-xyz-789
    python examples/analyze_reflections.py --reflection-type query_analysis
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict, Counter


class ReflectionLogAnalyzer:
    """Analyzes agent reflection logs"""
    
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
    
    def get_by_type(self, reflection_type: str) -> List[Dict[str, Any]]:
        """Get all reflections of a specific type"""
        return [e for e in self.entries 
                if e.get('data', {}).get('reflection_type') == reflection_type]
    
    def get_query_analyses(self) -> List[Dict[str, Any]]:
        """Get all query analysis reflections"""
        return self.get_by_type('query_analysis')
    
    def get_tool_decisions(self) -> List[Dict[str, Any]]:
        """Get all tool decision reflections"""
        return self.get_by_type('tool_decision')
    
    def get_query_reformulations(self) -> List[Dict[str, Any]]:
        """Get all query reformulation reflections"""
        return self.get_by_type('query_reformulation')
    
    def get_retrieval_evaluations(self) -> List[Dict[str, Any]]:
        """Get all retrieval evaluation reflections"""
        return self.get_by_type('retrieval_evaluation')
    
    def get_synthesis_decisions(self) -> List[Dict[str, Any]]:
        """Get all synthesis decision reflections"""
        return self.get_by_type('synthesis_decision')
    
    def get_session_flow(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all reflections for a session in chronological order"""
        session_entries = [e for e in self.entries if e.get('session_id') == session_id]
        return sorted(session_entries, key=lambda x: x.get('timestamp', ''))
    
    def get_intent_distribution(self) -> Dict[str, int]:
        """Get distribution of detected intents"""
        analyses = self.get_query_analyses()
        intents = [a.get('data', {}).get('detected_intent', 'unknown') 
                  for a in analyses]
        return dict(Counter(intents))
    
    def get_tool_usage_stats(self) -> Dict[str, Any]:
        """Get statistics about tool usage"""
        decisions = self.get_tool_decisions()
        
        tool_counts = Counter()
        confidence_by_tool = defaultdict(list)
        
        for decision in decisions:
            data = decision.get('data', {})
            tool = data.get('tool_name', 'unknown')
            confidence = data.get('confidence', 0)
            
            tool_counts[tool] += 1
            confidence_by_tool[tool].append(confidence)
        
        # Calculate average confidence per tool
        avg_confidence = {}
        for tool, confidences in confidence_by_tool.items():
            avg_confidence[tool] = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'tool_counts': dict(tool_counts),
            'avg_confidence': avg_confidence,
            'total_decisions': len(decisions)
        }
    
    def get_reformulation_patterns(self) -> List[Dict[str, Any]]:
        """Analyze query reformulation patterns"""
        reformulations = self.get_query_reformulations()
        
        patterns = []
        for ref in reformulations:
            data = ref.get('data', {})
            patterns.append({
                'original': data.get('original_query', ''),
                'reformulated': data.get('reformulated_query', ''),
                'reasoning': data.get('reasoning', ''),
                'timestamp': ref.get('timestamp', '')
            })
        
        return patterns
    
    def get_retrieval_quality_stats(self) -> Dict[str, Any]:
        """Get statistics about retrieval quality"""
        evaluations = self.get_retrieval_evaluations()
        
        total_results = []
        top_scores = []
        
        for eval in evaluations:
            data = eval.get('data', {})
            results_count = data.get('results_count', 0)
            scores = data.get('top_scores', [])
            
            total_results.append(results_count)
            if scores:
                top_scores.extend(scores)
        
        return {
            'total_evaluations': len(evaluations),
            'avg_results_count': sum(total_results) / len(total_results) if total_results else 0,
            'avg_top_score': sum(top_scores) / len(top_scores) if top_scores else 0,
            'min_score': min(top_scores) if top_scores else 0,
            'max_score': max(top_scores) if top_scores else 0
        }
    
    def get_confidence_distribution(self) -> Dict[str, int]:
        """Get distribution of confidence levels"""
        all_entries = []
        
        # Collect confidence from different reflection types
        for entry in self.entries:
            data = entry.get('data', {})
            confidence = data.get('confidence')
            if confidence is not None:
                all_entries.append(confidence)
        
        # Bucket into ranges
        buckets = {
            '0.0-0.2': 0,
            '0.2-0.4': 0,
            '0.4-0.6': 0,
            '0.6-0.8': 0,
            '0.8-1.0': 0
        }
        
        for conf in all_entries:
            if conf < 0.2:
                buckets['0.0-0.2'] += 1
            elif conf < 0.4:
                buckets['0.2-0.4'] += 1
            elif conf < 0.6:
                buckets['0.4-0.6'] += 1
            elif conf < 0.8:
                buckets['0.6-0.8'] += 1
            else:
                buckets['0.8-1.0'] += 1
        
        return buckets
    
    def print_summary(self):
        """Print comprehensive summary"""
        print("=" * 80)
        print("AGENT REFLECTION LOG ANALYSIS SUMMARY")
        print("=" * 80)
        print(f"Log file: {self.log_file}")
        print(f"Total entries: {len(self.entries)}")
        print()
        
        # Reflection type distribution
        print("-" * 80)
        print("REFLECTION TYPE DISTRIBUTION")
        print("-" * 80)
        type_counts = Counter(e.get('data', {}).get('reflection_type', 'unknown') 
                             for e in self.entries)
        for ref_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"{ref_type}: {count}")
        print()
        
        # Intent distribution
        print("-" * 80)
        print("DETECTED INTENT DISTRIBUTION")
        print("-" * 80)
        intents = self.get_intent_distribution()
        for intent, count in sorted(intents.items(), key=lambda x: x[1], reverse=True):
            print(f"{intent}: {count}")
        print()
        
        # Tool usage statistics
        print("-" * 80)
        print("TOOL USAGE STATISTICS")
        print("-" * 80)
        tool_stats = self.get_tool_usage_stats()
        print(f"Total tool decisions: {tool_stats['total_decisions']}")
        print("\nTool usage counts:")
        for tool, count in sorted(tool_stats['tool_counts'].items(), 
                                 key=lambda x: x[1], reverse=True):
            avg_conf = tool_stats['avg_confidence'].get(tool, 0)
            print(f"  {tool}: {count} times (avg confidence: {avg_conf:.2f})")
        print()
        
        # Retrieval quality
        print("-" * 80)
        print("RETRIEVAL QUALITY STATISTICS")
        print("-" * 80)
        retrieval = self.get_retrieval_quality_stats()
        print(f"Total evaluations: {retrieval['total_evaluations']}")
        print(f"Average results per query: {retrieval['avg_results_count']:.1f}")
        print(f"Average top score: {retrieval['avg_top_score']:.3f}")
        print(f"Score range: {retrieval['min_score']:.3f} - {retrieval['max_score']:.3f}")
        print()
        
        # Confidence distribution
        print("-" * 80)
        print("CONFIDENCE DISTRIBUTION")
        print("-" * 80)
        conf_dist = self.get_confidence_distribution()
        for range_label, count in conf_dist.items():
            bar = '█' * (count // 2) if count > 0 else ''
            print(f"{range_label}: {count:3d} {bar}")
        print()
        
        # Query reformulations
        print("-" * 80)
        print("QUERY REFORMULATION EXAMPLES")
        print("-" * 80)
        reformulations = self.get_reformulation_patterns()
        if reformulations:
            for i, ref in enumerate(reformulations[:5], 1):  # Show first 5
                print(f"{i}. Original: {ref['original']}")
                print(f"   Reformulated: {ref['reformulated']}")
                print(f"   Reasoning: {ref['reasoning']}")
                print()
        else:
            print("No query reformulations found")
        
        print("=" * 80)
    
    def print_session_flow(self, session_id: str):
        """Print reasoning flow for a specific session"""
        flow = self.get_session_flow(session_id)
        
        if not flow:
            print(f"No reflections found for session: {session_id}")
            return
        
        print("=" * 80)
        print(f"REASONING FLOW FOR SESSION: {session_id}")
        print("=" * 80)
        print()
        
        for i, entry in enumerate(flow, 1):
            timestamp = entry.get('timestamp', '')
            data = entry.get('data', {})
            ref_type = data.get('reflection_type', 'unknown')
            
            print(f"{i}. [{timestamp}] {ref_type.upper()}")
            print("-" * 80)
            
            if ref_type == 'query_analysis':
                print(f"Query: {data.get('original_query', '')}")
                print(f"Intent: {data.get('detected_intent', '')}")
                print(f"Requires tools: {data.get('requires_tools', False)}")
                print(f"Reasoning: {data.get('reasoning', '')}")
                print(f"Confidence: {data.get('confidence', 0):.2f}")
            
            elif ref_type == 'tool_decision':
                print(f"Tool: {data.get('tool_name', '')}")
                print(f"Rationale: {data.get('decision_rationale', '')}")
                print(f"Confidence: {data.get('confidence', 0):.2f}")
            
            elif ref_type == 'query_reformulation':
                print(f"Original: {data.get('original_query', '')}")
                print(f"Reformulated: {data.get('reformulated_query', '')}")
                print(f"Reasoning: {data.get('reasoning', '')}")
            
            elif ref_type == 'retrieval_evaluation':
                print(f"Query: {data.get('query', '')}")
                print(f"Results count: {data.get('results_count', 0)}")
                print(f"Top scores: {data.get('top_scores', [])}")
                print(f"Assessment: {data.get('relevance_assessment', '')}")
            
            elif ref_type == 'synthesis_decision':
                print(f"Sources used: {data.get('sources_used', 0)}")
                print(f"Confidence: {data.get('confidence', 0):.2f}")
                print(f"Reasoning: {data.get('reasoning', '')}")
            
            print()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze agent reflection logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze default log file
  python examples/analyze_reflections.py
  
  # Analyze specific log file
  python examples/analyze_reflections.py --log-file logs/agent_reflections.log
  
  # Show reasoning flow for a session
  python examples/analyze_reflections.py --session-id session-xyz-789
  
  # Filter by reflection type
  python examples/analyze_reflections.py --reflection-type query_analysis
  
  # Output as JSON
  python examples/analyze_reflections.py --json
        """
    )
    
    parser.add_argument(
        '--log-file',
        default='logs/agent_reflections.log',
        help='Path to agent reflection log file (default: logs/agent_reflections.log)'
    )
    
    parser.add_argument(
        '--session-id',
        help='Show reasoning flow for specific session'
    )
    
    parser.add_argument(
        '--reflection-type',
        choices=['query_analysis', 'tool_decision', 'query_reformulation', 
                'retrieval_evaluation', 'synthesis_decision'],
        help='Filter by reflection type'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    args = parser.parse_args()
    
    analyzer = ReflectionLogAnalyzer(args.log_file)
    
    if args.session_id:
        # Show session flow
        analyzer.print_session_flow(args.session_id)
    
    elif args.reflection_type:
        # Show specific reflection type
        entries = analyzer.get_by_type(args.reflection_type)
        print(f"Found {len(entries)} {args.reflection_type} reflections")
        print()
        for entry in entries:
            print(json.dumps(entry, indent=2, ensure_ascii=False))
            print()
    
    elif args.json:
        # Output as JSON
        result = {
            'total_entries': len(analyzer.entries),
            'intent_distribution': analyzer.get_intent_distribution(),
            'tool_usage': analyzer.get_tool_usage_stats(),
            'retrieval_quality': analyzer.get_retrieval_quality_stats(),
            'confidence_distribution': analyzer.get_confidence_distribution(),
            'reformulation_patterns': analyzer.get_reformulation_patterns()
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        # Print summary
        analyzer.print_summary()


if __name__ == '__main__':
    main()
