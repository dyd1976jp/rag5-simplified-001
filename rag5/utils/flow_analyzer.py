"""
Flow log analyzer for unified flow logs.

This module provides utilities for analyzing, filtering, and extracting
information from unified flow log files.
"""

import json
import csv
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from collections import defaultdict
import statistics


class FlowLogAnalyzer:
    """
    Analyzer for unified flow logs.
    
    Provides utilities for filtering, extracting, and analyzing
    information from unified flow log files.
    
    This analyzer can:
    - Filter logs by session_id
    - Calculate timing statistics
    - Find errors and slow operations
    - Export logs to JSON and CSV formats
    
    Attributes:
        log_file: Path to unified flow log file
        entries: Parsed log entries
        
    Example:
        >>> from rag5.utils.flow_analyzer import FlowLogAnalyzer
        >>> 
        >>> # Create analyzer
        >>> analyzer = FlowLogAnalyzer("logs/unified_flow.log")
        >>> 
        >>> # Filter by session
        >>> session_entries = analyzer.filter_by_session("abc-123-def")
        >>> 
        >>> # Get timing statistics
        >>> stats = analyzer.get_timing_stats()
        >>> print(f"Average query time: {stats['query_complete']['avg']:.2f}s")
        >>> 
        >>> # Find errors
        >>> errors = analyzer.find_errors()
        >>> print(f"Found {len(errors)} errors")
        >>> 
        >>> # Export to JSON
        >>> analyzer.export_to_json("output.json")
    """
    
    # Regular expressions for parsing log entries
    ENTRY_START_PATTERN = re.compile(
        r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\] '
        r'(\w+)'
        r'(?: \(Session: ([^)]+)\))?'
        r'(?: \[\+(\d+\.\d+)s\])?'
    )
    
    SESSION_PATTERN = re.compile(r'Session: ([^\)]+)')
    DURATION_PATTERN = re.compile(r'Duration: (\d+\.\d+)s')
    STATUS_PATTERN = re.compile(r'Status: (\w+)')
    TOOL_PATTERN = re.compile(r'Tool: (.+)')
    MODEL_PATTERN = re.compile(r'Model: (.+)')
    
    def __init__(self, log_file: str):
        """
        Initialize analyzer.
        
        Args:
            log_file: Path to unified flow log file
        """
        self.log_file = log_file
        self.entries: List[Dict[str, Any]] = []
        
        # Parse log file on initialization
        self._parse_log_file()
    
    def _parse_log_file(self) -> None:
        """
        Parse the log file and structure log entries.
        
        Reads the unified flow log file and extracts structured information
        from each entry, storing them in memory for analysis.
        
        Each parsed entry is a dictionary with keys:
        - timestamp: datetime object
        - event_type: string (e.g., "QUERY_START", "TOOL_EXECUTION")
        - session_id: string (if available)
        - elapsed_time: float (if available)
        - raw_content: string (full entry text)
        - metadata: dict (event-specific data)
        """
        log_path = Path(self.log_file)
        
        if not log_path.exists():
            # Empty log file - no entries to parse
            return
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by separator lines to get individual entries
            # Entries are separated by "=" * 80
            separator = "=" * 80
            raw_entries = content.split(separator)
            
            # Track current session for entries that don't have explicit session_id
            current_session = None
            
            for raw_entry in raw_entries:
                raw_entry = raw_entry.strip()
                if not raw_entry:
                    continue
                
                # Parse the entry
                entry = self._parse_entry(raw_entry)
                if entry:
                    # If entry has session_id, update current session
                    if entry.get('session_id'):
                        current_session = entry['session_id']
                    # If entry doesn't have session_id but we have a current session, use it
                    elif current_session:
                        entry['session_id'] = current_session
                    
                    self.entries.append(entry)
                    
        except Exception as e:
            # Log parsing errors but don't fail
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to parse log file {self.log_file}: {e}", exc_info=True)
    
    def _parse_entry(self, raw_entry: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single log entry.
        
        Args:
            raw_entry: Raw entry text
            
        Returns:
            Parsed entry dictionary or None if parsing fails
        """
        lines = raw_entry.split('\n')
        if not lines:
            return None
        
        # Parse the header line
        header_line = lines[0]
        match = self.ENTRY_START_PATTERN.match(header_line)
        
        if not match:
            return None
        
        timestamp_str, event_type, session_id, elapsed_time_str = match.groups()
        
        # Parse timestamp
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            timestamp = None
        
        # Parse elapsed time
        elapsed_time = float(elapsed_time_str) if elapsed_time_str else None
        
        # Extract session_id from content if not in header
        if not session_id:
            session_match = self.SESSION_PATTERN.search(raw_entry)
            if session_match:
                session_id = session_match.group(1)
        
        # Build entry dictionary
        entry = {
            'timestamp': timestamp,
            'event_type': event_type,
            'session_id': session_id,
            'elapsed_time': elapsed_time,
            'raw_content': raw_entry,
            'metadata': {}
        }
        
        # Extract event-specific metadata
        entry['metadata'] = self._extract_metadata(event_type, raw_entry)
        
        return entry
    
    def _extract_metadata(self, event_type: str, content: str) -> Dict[str, Any]:
        """
        Extract event-specific metadata from entry content.
        
        Args:
            event_type: Type of event
            content: Entry content
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Extract common fields
        duration_match = self.DURATION_PATTERN.search(content)
        if duration_match:
            metadata['duration'] = float(duration_match.group(1))
        
        status_match = self.STATUS_PATTERN.search(content)
        if status_match:
            metadata['status'] = status_match.group(1)
        
        # Extract event-specific fields
        if event_type in ('TOOL_EXECUTION', 'TOOL_EXEC'):
            tool_match = self.TOOL_PATTERN.search(content)
            if tool_match:
                metadata['tool_name'] = tool_match.group(1)
        
        elif event_type == 'LLM_CALL':
            model_match = self.MODEL_PATTERN.search(content)
            if model_match:
                metadata['model'] = model_match.group(1)
        
        elif event_type == 'ERROR':
            # Extract error type and message
            lines = content.split('\n')
            for line in lines:
                if line.startswith('Error Type:'):
                    metadata['error_type'] = line.split(':', 1)[1].strip()
                elif line.startswith('Message:'):
                    metadata['error_message'] = line.split(':', 1)[1].strip()
        
        elif event_type in ('QUERY_COMPLETE', 'COMPLETE'):
            # Extract total duration
            if 'duration' in metadata:
                metadata['total_duration'] = metadata['duration']
        
        return metadata
    
    def filter_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Extract all entries for a specific session.
        
        Args:
            session_id: Session ID to filter by
            
        Returns:
            List of log entries for the session
        """
        return [
            entry for entry in self.entries
            if entry.get('session_id') == session_id
        ]
    
    def get_timing_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate timing statistics across all queries.
        
        Calculates average, min, max, and p95 durations for:
        - Tool executions
        - LLM calls
        - Total query time
        
        Returns:
            Dictionary with timing statistics for each operation type
        """
        # Collect durations by operation type
        tool_durations = []
        llm_durations = []
        query_durations = []
        
        for entry in self.entries:
            event_type = entry['event_type']
            metadata = entry.get('metadata', {})
            
            if event_type in ('TOOL_EXECUTION', 'TOOL_EXEC'):
                duration = metadata.get('duration')
                if duration is not None:
                    tool_durations.append(duration)
            
            elif event_type == 'LLM_CALL':
                duration = metadata.get('duration')
                if duration is not None:
                    llm_durations.append(duration)
            
            elif event_type in ('QUERY_COMPLETE', 'COMPLETE'):
                duration = metadata.get('total_duration') or entry.get('elapsed_time')
                if duration is not None:
                    query_durations.append(duration)
        
        # Calculate statistics
        stats = {}
        
        if tool_durations:
            stats['tool_execution'] = self._calculate_stats(tool_durations)
        
        if llm_durations:
            stats['llm_call'] = self._calculate_stats(llm_durations)
        
        if query_durations:
            stats['query_complete'] = self._calculate_stats(query_durations)
        
        return stats
    
    def _calculate_stats(self, durations: List[float]) -> Dict[str, float]:
        """
        Calculate statistics for a list of durations.
        
        Args:
            durations: List of duration values
            
        Returns:
            Dictionary with avg, min, max, p95 statistics
        """
        if not durations:
            return {
                'count': 0,
                'avg': 0.0,
                'min': 0.0,
                'max': 0.0,
                'p95': 0.0
            }
        
        sorted_durations = sorted(durations)
        p95_index = int(len(sorted_durations) * 0.95)
        
        return {
            'count': len(durations),
            'avg': statistics.mean(durations),
            'min': min(durations),
            'max': max(durations),
            'p95': sorted_durations[p95_index] if p95_index < len(sorted_durations) else sorted_durations[-1]
        }
    
    def find_errors(self) -> List[Dict[str, Any]]:
        """
        Find all error entries in the log.
        
        Returns:
            List of error entries with context
        """
        errors = []
        
        for entry in self.entries:
            if entry['event_type'] == 'ERROR':
                errors.append({
                    'timestamp': entry['timestamp'],
                    'session_id': entry.get('session_id'),
                    'elapsed_time': entry.get('elapsed_time'),
                    'error_type': entry['metadata'].get('error_type'),
                    'error_message': entry['metadata'].get('error_message'),
                    'raw_content': entry['raw_content']
                })
        
        return errors
    
    def find_slow_operations(
        self,
        threshold_seconds: float = 5.0
    ) -> List[Dict[str, Any]]:
        """
        Find operations that exceeded a time threshold.
        
        Args:
            threshold_seconds: Time threshold in seconds
            
        Returns:
            List of slow operations
        """
        slow_ops = []
        
        for entry in self.entries:
            event_type = entry['event_type']
            metadata = entry.get('metadata', {})
            
            # Check duration for operations that have it
            duration = None
            operation_name = None
            
            if event_type in ('TOOL_EXECUTION', 'TOOL_EXEC'):
                duration = metadata.get('duration')
                operation_name = f"Tool: {metadata.get('tool_name', 'unknown')}"
            
            elif event_type == 'LLM_CALL':
                duration = metadata.get('duration')
                operation_name = f"LLM: {metadata.get('model', 'unknown')}"
            
            elif event_type in ('QUERY_COMPLETE', 'COMPLETE'):
                duration = metadata.get('total_duration') or entry.get('elapsed_time')
                operation_name = "Query"
            
            # Add to slow operations if exceeds threshold
            if duration is not None and duration >= threshold_seconds:
                slow_ops.append({
                    'timestamp': entry['timestamp'],
                    'session_id': entry.get('session_id'),
                    'event_type': event_type,
                    'operation': operation_name,
                    'duration': duration,
                    'threshold': threshold_seconds,
                    'raw_content': entry['raw_content']
                })
        
        return slow_ops
    
    def export_to_json(self, output_file: str) -> None:
        """
        Export log to structured JSON format.
        
        Args:
            output_file: Output file path
        """
        try:
            # Convert entries to JSON-serializable format
            json_entries = []
            for entry in self.entries:
                json_entry = {
                    'timestamp': entry['timestamp'].isoformat() if entry['timestamp'] else None,
                    'event_type': entry['event_type'],
                    'session_id': entry.get('session_id'),
                    'elapsed_time': entry.get('elapsed_time'),
                    'metadata': entry.get('metadata', {}),
                    'raw_content': entry['raw_content']
                }
                json_entries.append(json_entry)
            
            # Write to file
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_entries, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to export to JSON: {e}", exc_info=True)
            raise
    
    def export_to_csv(self, output_file: str) -> None:
        """
        Export log to CSV format.
        
        Exports key metrics in a tabular format suitable for spreadsheet analysis.
        
        Args:
            output_file: Output file path
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Timestamp',
                    'Event Type',
                    'Session ID',
                    'Elapsed Time (s)',
                    'Duration (s)',
                    'Status',
                    'Operation',
                    'Details'
                ])
                
                # Write entries
                for entry in self.entries:
                    metadata = entry.get('metadata', {})
                    
                    # Determine operation name
                    operation = ''
                    details = ''
                    
                    if entry['event_type'] in ('TOOL_EXECUTION', 'TOOL_EXEC'):
                        operation = metadata.get('tool_name', '')
                        details = f"Tool execution"
                    elif entry['event_type'] == 'LLM_CALL':
                        operation = metadata.get('model', '')
                        details = f"LLM call"
                    elif entry['event_type'] == 'ERROR':
                        operation = metadata.get('error_type', '')
                        details = metadata.get('error_message', '')
                    elif entry['event_type'] in ('QUERY_START', 'QUERY_COMPLETE', 'COMPLETE'):
                        operation = 'Query'
                        details = metadata.get('status', '')
                    
                    writer.writerow([
                        entry['timestamp'].isoformat() if entry['timestamp'] else '',
                        entry['event_type'],
                        entry.get('session_id', ''),
                        f"{entry.get('elapsed_time', ''):.3f}" if entry.get('elapsed_time') is not None else '',
                        f"{metadata.get('duration', ''):.3f}" if metadata.get('duration') is not None else '',
                        metadata.get('status', ''),
                        operation,
                        details
                    ])
                    
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to export to CSV: {e}", exc_info=True)
            raise
