# Flow Log Analyzer CLI

Command-line interface for analyzing unified flow logs from the RAG5 system.

## Installation

The CLI is included in the `scripts` directory and uses the `rag5.utils.flow_analyzer` module.

## Usage

```bash
python scripts/analyze_flow_logs.py --log-file <path> [options]
```

### Required Arguments

- `--log-file PATH` - Path to unified flow log file

### Analysis Commands

- `--session SESSION_ID` - Filter log entries by session ID
- `--stats` - Show timing statistics
- `--errors` - Show all errors
- `--slow THRESHOLD` - Find slow operations exceeding THRESHOLD seconds

### Export Commands

- `--export-json FILE` - Export log entries to JSON file
- `--export-csv FILE` - Export log entries to CSV file

## Examples

### Show Timing Statistics

```bash
python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log --stats
```

Output:
```
================================================================================
                               Timing Statistics                                
================================================================================

--------------------------------------------------------------------------------
Tool Execution
--------------------------------------------------------------------------------
  Count:       4
  Average:     3.51s
  Minimum:     234ms
  Maximum:     6.79s
  P95:         6.79s

--------------------------------------------------------------------------------
Llm Call
--------------------------------------------------------------------------------
  Count:       2
  Average:     1.57s
  Minimum:     1.57s
  Maximum:     1.57s
  P95:         1.57s

--------------------------------------------------------------------------------
Query Complete
--------------------------------------------------------------------------------
  Count:       6
  Average:     3.64s
  Minimum:     567ms
  Maximum:     8.23s
  P95:         8.23s
```

### Filter by Session

```bash
python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log --session test-session-001
```

Output:
```
================================================================================
                        Session Filter: test-session-001                        
================================================================================

Found 6 entries for session test-session-001

Timeline:
      Time  Event Type                      Details                                 
-------------------------------------------------------------------------------------
    0.000s  QUERY_START                                                             
    0.000s  QUERY_ANALYSIS                                                          
    0.001s  TOOL_SELECTION                                                          
    0.001s  TOOL_EXECUTION                  knowledge_base_search [234ms] SUCCESS   
    0.001s  LLM_CALL                        qwen2.5:7b [1.57s]                      
    2.123s  QUERY_COMPLETE                  SUCCESS [total: 2.12s]
```

### Find Errors

```bash
python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log --errors
```

Output:
```
================================================================================
                                  Error Report                                  
================================================================================

Found 1 error(s):

--------------------------------------------------------------------------------
Error 1
--------------------------------------------------------------------------------
  Session:     test-session-002
  Timestamp:   2025-11-10 21:34:58.804000
  Elapsed:     0ms
  Type:        ToolExecutionError
  Message:     Failed to connect to API
```

### Find Slow Operations

```bash
python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log --slow 5.0
```

Output:
```
================================================================================
                            Slow Operations (>5.00s)                            
================================================================================

Found 2 slow operation(s):

Operation                                     Duration  Session                       
-------------------------------------------------------------------------------------
Tool: complex_search                             6.79s  test-session-003              
Query                                            8.23s  test-session-003
```

### Export to JSON

```bash
python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log --export-json output.json
```

Output:
```
================================================================================
                                 Export to JSON                                 
================================================================================

✓ Successfully exported to: output.json
  Entries:     12
  File size:   5,797 bytes
```

### Export to CSV

```bash
python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log --export-csv output.csv
```

Output:
```
================================================================================
                                 Export to CSV                                  
================================================================================

✓ Successfully exported to: output.csv
  Entries:     12
  File size:   2,204 bytes
```

### Combine Multiple Commands

You can combine multiple analysis commands in a single invocation:

```bash
python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log --stats --errors --slow 3.0
```

This will:
1. Show timing statistics
2. Show all errors
3. Find operations slower than 3 seconds

## CSV Output Format

The CSV export includes the following columns:

- **Timestamp** - When the event occurred (ISO format)
- **Event Type** - Type of event (QUERY_START, TOOL_EXECUTION, etc.)
- **Session ID** - Session identifier
- **Elapsed Time (s)** - Time since query start
- **Duration (s)** - Operation duration (if applicable)
- **Status** - Operation status (SUCCESS, ERROR, etc.)
- **Operation** - Operation name (tool name, model name, etc.)
- **Details** - Additional details

## JSON Output Format

The JSON export includes structured data for each log entry:

```json
[
  {
    "timestamp": "2025-11-10T21:34:58.803000",
    "event_type": "QUERY_START",
    "session_id": "test-session-001",
    "elapsed_time": 0.0,
    "metadata": {},
    "raw_content": "[2025-11-10 21:34:58.803] QUERY_START..."
  },
  ...
]
```

## Error Handling

### Log File Not Found

```bash
$ python scripts/analyze_flow_logs.py --log-file nonexistent.log --stats
Error: Log file not found: nonexistent.log
```

### No Command Specified

```bash
$ python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log
Error: At least one command must be specified
```

Use `--help` to see available commands.

## Tips

1. **Performance Analysis**: Use `--stats` to get an overview of system performance
2. **Debugging**: Use `--session SESSION_ID` to trace a specific query through the system
3. **Error Investigation**: Use `--errors` to quickly find all failures
4. **Optimization**: Use `--slow THRESHOLD` to identify bottlenecks
5. **Data Export**: Use `--export-csv` for spreadsheet analysis or `--export-json` for programmatic processing

## See Also

- [FlowLogAnalyzer Documentation](../docs/flow_log_analyzer.md)
- [Unified Flow Logging Guide](../docs/unified_flow_logging.md)
- [FlowLogger Integration](../docs/flow_logger_integration.md)
